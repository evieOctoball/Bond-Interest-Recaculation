import pandas as pd
import numpy as np
import cv2
import pytesseract
from PIL import Image
from thefuzz import process, fuzz
import os

# ==========================================
# 1. Enfusion 截图 OCR 提取模块
# ==========================================
def extract_enfusion_from_image(image_path):
    """
    从 Enfusion 截图提取 Issuer 和 Base Amount
    如遇到复杂表格截图，推荐使用 easyocr 或 paddleocr 以提高精度
    """
    # 读取图片
    img = Image.open(image_path)
    
    # OCR 文本识别
    text = pytesseract.image_to_string(img, lang='eng')
    
    rows = []
    for line in text.split('\n'):
        line = line.strip()
        if not line or "Risk Issuer" in line or "Base Amount" in line:
            continue
        
        # 提取金额（通常位于行末）
        parts = line.rsplit(' ', 1)
        if len(parts) == 2:
            issuer = parts[0].strip()
            amount_str = parts[1].replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
            try:
                amount = float(amount_str)
                rows.append({"ENFUSION_ISSUER": issuer, "ENFUSION_AMOUNT": amount})
            except ValueError:
                continue
                
    return pd.DataFrame(rows)


# ==========================================
# 2. Apex PDF / Excel 解析模块
# ==========================================
def parse_apex_file(file_path):
    """
    解析 Apex 发送的 Bond Interest 文件 (Excel/PDF)
    """
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        # 读取 Excel 文件，自动跳过表头说明行
        df = pd.read_excel(file_path, skiprows=3)
        # 清洗列名
        df.columns = [str(c).strip() for c in df.columns]
        
        # 寻找债券名称列与利息金额列
        # 根据实际列名微调
        name_col = [c for c in df.columns if 'Quantity' in c or 'Identifier' in c or 'BOND' in c][0]
        amount_col = df.columns[-1] # 通常最后一列为 USD 应计利息
        
        apex_data = df[[name_col, amount_col]].dropna()
        apex_data.columns = ['APEX_NAME', 'APEX_AMOUNT']
        
        # 清洗金额
        apex_data['APEX_AMOUNT'] = pd.to_numeric(apex_data['APEX_AMOUNT'], errors='coerce')
        return apex_data
    else:
        # 如果是 PDF 文件，可配合 pdfplumber 提取表格
        import pdfplumber
        rows = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # 假设解析出名称与金额
                        if len(row) >= 2:
                            rows.append({'APEX_NAME': row[2], 'APEX_AMOUNT': row[-1]})
        df = pd.DataFrame(rows)
        return df


# ==========================================
# 3. 对账匹配与逻辑对比模块
# ==========================================
def reconcile_bond_interest(enfusion_df, apex_df, mapping_df, tolerance=0.02):
    """
    核心对账逻辑：通过映射表及模糊匹配将 Enfusion 与 Apex 数据打通并比对
    """
    # 建立映射字典
    mapping_dict = dict(zip(mapping_df['APEX'].astype(str).str.strip(), 
                            mapping_df['ENFUSION'].astype(str).str.strip()))
    
    # 步骤 1: 使用映射表匹配
    apex_df['MATCHED_ENFUSION_NAME'] = apex_df['APEX_NAME'].map(mapping_dict)
    
    # 步骤 2: 未选中的使用模糊匹配 (Fuzzy Matching) 补充兜底
    unmatched_apex = apex_df[apex_df['MATCHED_ENFUSION_NAME'].isna()]
    enfusion_names = enfusion_df['ENFUSION_ISSUER'].tolist()
    
    for idx, row in unmatched_apex.iterrows():
        apex_name = str(row['APEX_NAME'])
        match, score = process.extractOne(apex_name, enfusion_names, scorer=fuzz.token_set_ratio)
        if score > 75:  # 匹配度高于 75 分视作同一家 Issuer
            apex_df.loc[idx, 'MATCHED_ENFUSION_NAME'] = match

    # 步骤 3: Full Outer Join 合并两端数据
    merged = pd.merge(
        enfusion_df, 
        apex_df, 
        left_on='ENFUSION_ISSUER', 
        right_on='MATCHED_ENFUSION_NAME', 
        how='outer'
    )

    # 步骤 4: 计算金额差异与状态
    merged['ENFUSION_AMOUNT'] = merged['ENFUSION_AMOUNT'].fillna(0.0)
    merged['APEX_AMOUNT'] = merged['APEX_AMOUNT'].fillna(0.0)
    merged['DIFF'] = (merged['ENFUSION_AMOUNT'] - merged['APEX_AMOUNT']).round(2)
    
    def check_status(row):
        if pd.isna(row['ENFUSION_ISSUER']):
            return 'Only in Apex'
        if pd.isna(row['APEX_NAME']):
            return 'Only in Enfusion'
        if abs(row['DIFF']) <= tolerance:
            return 'Matched'
        return 'Mismatch'

    merged['STATUS'] = merged.apply(check_status, axis=1)
    
    # 整理显示列名
    result_df = merged[['ENFUSION_ISSUER', 'APEX_NAME', 'ENFUSION_AMOUNT', 'APEX_AMOUNT', 'DIFF', 'STATUS']]
    return result_df


# ==========================================
# 4. 主程序运行示例
# ==========================================
if __name__ == "__main__":
    # 1. 读取 mapping 表
    mapping_df = pd.read_excel("Apex Name & Enfusion Name.xlsx")
    
    # 2. 读取 Apex 数据 (Excel/PDF)
    apex_df = parse_apex_file("APEX_20261030_Bond Interest Calculation.xlsx")
    
    # 3. 提取 Enfusion 截图数据 (或直接读取预解析结果)
    # enfusion_df = extract_enfusion_from_image("enfusion_screenshot.png")
    
    # 示例临时 Mock Enfusion 数据（实际运行请使用提取函数）
    enfusion_df = pd.DataFrame([
        {"ENFUSION_ISSUER": "CAS CAPITAL NO. 2 LIMITED", "ENFUSION_AMOUNT": 8854.17},
        {"ENFUSION_ISSUER": "CENTRAL PLAZA DEVELOPMENT LTD", "ENFUSION_AMOUNT": 33160.83},
        {"ENFUSION_ISSUER": "CHINALCO CAPITAL HOLDINGS LTD", "ENFUSION_AMOUNT": 866.67},
        {"ENFUSION_ISSUER": "CHIYU BANKING CORP LTD", "ENFUSION_AMOUNT": 21179.86},
        {"ENFUSION_ISSUER": "BAUHINIA ILBS 2 LTD", "ENFUSION_AMOUNT": 2061.14}
    ])
    
    # 4. 运行对账
    recon_result = reconcile_bond_interest(enfusion_df, apex_df, mapping_df)
    
    # 5. 输出对账结果 Excel 文件
    recon_result.to_excel("Bond_Interest_Reconciliation_Result.xlsx", index=False)
    print("对账完成！前10条对账结果如下：")
    print(recon_result.head(10))

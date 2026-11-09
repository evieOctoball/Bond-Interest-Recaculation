import streamlit as st
import pandas as pd
from thefuzz import process, fuzz
import pdfplumber

st.set_page_config(page_title="Bond Interest Reconciliation", layout="wide")

st.title("Bond Interest 对账系统")
st.markdown("上传 **Apex 报表 (Excel/PDF)**、**Enfusion 截图或数据** 以及 **映射表**，系统将自动完成匹配和差异比对。")

# --- 侧边栏：文件上传 ---
st.sidebar.header("1. 上传对账文件")
mapping_file = st.sidebar.file_uploader("上传映射表 (Apex Name & Enfusion Name.xlsx)", type=["xlsx"])
apex_file = st.sidebar.file_uploader("上传 Apex 报告 (Excel/PDF)", type=["xlsx", "xls", "pdf"])

# 模拟 Enfusion 输入（也可以通过上传文本或截图）
st.sidebar.header("2. 输入 Enfusion 数据")
enfusion_input_mode = st.sidebar.radio("选择 Enfusion 数据录入方式", ["手动录入/粘贴模拟数据", "上传 Enfusion 截图 (OCR)"])

# --- 主界面逻辑 ---
if mapping_file and apex_file:
    # 1. 读取映射表
    mapping_df = pd.read_excel(mapping_file)
    
    # 2. 读取 Apex 文件
    if apex_file.name.endswith('.xlsx') or apex_file.name.endswith('.xls'):
        df_apex = pd.read_excel(apex_file, skiprows=3)
        df_apex.columns = [str(c).strip() for c in df_apex.columns]
        name_col = [c for c in df_apex.columns if 'Quantity' in c or 'Identifier' in c or 'BOND' in c][0]
        amount_col = df_apex.columns[-1]
        apex_df = df_apex[[name_col, amount_col]].dropna()
        apex_df.columns = ['APEX_NAME', 'APEX_AMOUNT']
        apex_df['APEX_AMOUNT'] = pd.to_numeric(apex_df['APEX_AMOUNT'], errors='coerce')
    else:
        # PDF 解析示例
        rows = []
        with pdfplumber.open(apex_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if len(row) >= 2:
                            rows.append({'APEX_NAME': row[2], 'APEX_AMOUNT': row[-1]})
        apex_df = pd.DataFrame(rows)
        apex_df['APEX_AMOUNT'] = pd.to_numeric(apex_df['APEX_AMOUNT'], errors='coerce')

    # 3. 获取 Enfusion 数据
    if enfusion_input_mode == "手动录入/粘贴模拟数据":
        # 默认填入你截图里的部分数据方便测试
        default_data = """CAS CAPITAL NO. 2 LIMITED, 8854.17
CENTRAL PLAZA DEVELOPMENT LTD, 33160.83
CHINALCO CAPITAL HOLDINGS LTD, 866.67
CHIYU BANKING CORP LTD, 21179.86
BAUHINIA ILBS 2 LTD, 2061.14
BOC Aviation Ltd, 19833.33"""
        
        user_text = st.text_area("在此粘贴 Enfusion 的 Issuer 与金额 (格式: Issuer, Amount 每行一条)", value=default_data, height=150)
        
        enfusion_rows = []
        for line in user_text.split('\n'):
            if ',' in line:
                parts = line.split(',')
                try:
                    enfusion_rows.append({"ENFUSION_ISSUER": parts[0].strip(), "ENFUSION_AMOUNT": float(parts[1].strip().replace('$', '').replace(',', ''))})
                except ValueError:
                    continue
        enfusion_df = pd.DataFrame(enfusion_rows)
    else:
        st.info("OCR 截图识别功能可配合 pytesseract 使用（如果在线部署，建议先用上面的文本/表格模拟测试）")
        enfusion_df = pd.DataFrame(columns=["ENFUSION_ISSUER", "ENFUSION_AMOUNT"])

    # --- 开始对账计算按钮 ---
    if not enfusion_df.empty and st.button("开始执行对账", type="primary"):
        # 映射字典
        mapping_dict = dict(zip(mapping_df['APEX'].astype(str).str.strip(), 
                                mapping_df['ENFUSION'].astype(str).str.strip()))
        
        apex_df['MATCHED_ENFUSION_NAME'] = apex_df['APEX_NAME'].map(mapping_dict)
        
        # 模糊匹配兜底
        unmatched_apex = apex_df[apex_df['MATCHED_ENFUSION_NAME'].isna()]
        enfusion_names = enfusion_df['ENFUSION_ISSUER'].tolist()
        
        for idx, row in unmatched_apex.iterrows():
            apex_name = str(row['APEX_NAME'])
            if enfusion_names:
                match, score = process.extractOne(apex_name, enfusion_names, scorer=fuzz.token_set_ratio)
                if score > 75:
                    apex_df.loc[idx, 'MATCHED_ENFUSION_NAME'] = match

        # 合并
        merged = pd.merge(enfusion_df, apex_df, left_on='ENFUSION_ISSUER', right_on='MATCHED_ENFUSION_NAME', how='outer')
        merged['ENFUSION_AMOUNT'] = merged['ENFUSION_AMOUNT'].fillna(0.0)
        merged['APEX_AMOUNT'] = merged['APEX_AMOUNT'].fillna(0.0)
        merged['DIFF'] = (merged['ENFUSION_AMOUNT'] - merged['APEX_AMOUNT']).round(2)
        
        def check_status(row):
            if pd.isna(row['ENFUSION_ISSUER']): return 'Only in Apex'
            if pd.isna(row['APEX_NAME']): return 'Only in Enfusion'
            if abs(row['DIFF']) <= 0.02: return 'Matched'
            return 'Mismatch'

        merged['STATUS'] = merged.apply(check_status, axis=1)
        result_df = merged[['ENFUSION_ISSUER', 'APEX_NAME', 'ENFUSION_AMOUNT', 'APEX_AMOUNT', 'DIFF', 'STATUS']]
        
        # 展示结果
        st.subheader("📊 对账结果概览")
        st.dataframe(result_df, use_container_width=True)
        
        # 下载按钮
        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 下载对账结果 CSV", data=csv, file_name="reconciliation_result.csv", mime="text/csv")
else:
        st.warning("请先在左侧侧边栏上传【映射表】和【Apex 报告文件】。")

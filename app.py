import streamlit as st
import pandas as pd
from thefuzz import process, fuzz

st.set_page_config(page_title="Bond Interest Reconciliation", layout="wide")

st.title("Bond Interest 对账系统")

# 1. 固定的 Enfusion 债券标准列表
DEFAULT_ENFUSION_ISSUERS = [
    DEFAULT_ENFUSION_ISSUERS = [
    "ACHIEVER INVESTMENT LTD",
    "ANHUI TRANSPORTATION HOLDING GROUP HK LTD",
    "BAUHINIA ILBS 2 LTD",
    "BEIJING GAS SINGAPORE CAPITAL CORP",
    "BOC Aviation Ltc",
    "Bank of Qingdao Co Ltd",
    "CALC BOND 3 LTD",
    "CALC BONDS LTD",
    "CAS CAPITAL NO. 2 LIMITED",
    "CENTRAL INTERNATIONAL DEVELOPMENT (BVI) LTD",
    "CENTRAL PLAZA DEVELOPMENT LTD",
    "CHINA CINDA (2020)IMANAGEMENT LTD",
    "CHINA ENERGY RESERVE AND CHEMICALS GROUP CO LTD",
    "CHINA GEZHOUBA GROUP HONG KONG OVERSEAS INVESTMENT CO LTD",
    "CHINA GREAT WALL INTERNATIONAL HOLDINGS VI LTD",
    "CHINA HUANENG GROUP (HONG KONG) TREASURY MANAGEMENT HOLDING LTD",
    "CHINA OVERSEAS GRAND OCEANS FINANCE IV CAYMAN LTD",
    "CHINALCO CAPITAL HOLDINGS LTD",
    "XIAIB 8.000 Perp '27 FRN - CIBHK",
    "XIAIB 5.750 04/07/32'27 FRN - CISL",
    "CHONGQING NAN'AN DISTRICT URBAN CONSTRUCTION DEVELOPMENT (GROUP) CO.",
    "CHONGQING WESTEN MODERN LOGISTICS INDUSTRY PARK DEVELOPMENT CO LTD",
    "CHOUZHOU INTERNATIONAL INVESTMENT LTD",
    "CITIC KA WAH BANK LTD",
    "COASTAL EMERALD LIMITED",
    "Cathay Pacific MTN Financing HK Ltd",
    "China Cinda Asset Management Co Ltd",
    "China Hongqiao Group Ltd",
    "China Oil and Gas Group Ltd",
    "China Resources Land Limited",
    "China South City Holdings Ltd",
    "China Water Affairs Group Ltd",
    "Chong Hing Bank Ltd",
    "Deutsche Bank AG",
    "ELECT GLOBAL INVESTMENTS LTD",
    "FORTUNE STAR (BVI) LTD",
    "FRANSHION BRILLIANT LTD",
    "FWD Group Holdings Ltd",
    "GF GLOBAL CAPITAL LTD",
    "GLP Pte. Ltd.",
    "GOLDEN CONCORD GROUP LTD",
    "GREENLAND GLOBAL INVESTMENT LTD",
    "GUANG TAO INVESTMENT LTD",
    "GUANGXI FINANCIAL INVESTMENT GROUP CO LTD",
    "GUOTAI JUNAN FINANCIAL PRODUCTS LTD",
    "Greentown China Holdings Limited",
    "Guangzhou Development Group Inc",
    "Guotai Junan International Holdings Ltd",
    "HAITIAN (BVI) INTERNATIONAL INVESTMENT DEVELOPMENT LTD",
    "HKTCP 5.125 06/10/36 '36 MTN",
    "HKTCP 5.125 06/10/36 '36 MTN",
    "HONGKONG INTERNATIONAL QINGDAO CO LTD",
    "HONGKONG XIANGYU INVESTMENT CO LTD",
    "HOPSON CAPITAL INTERNATIONAL GROUP CO LTD",
    "HSBC Holdings PLC",
    "HSBA6.750 Perp '32 FRN",
    "HSBA6.750 Perp '30 FRN",
    "HSBA7.050 Perp '30 FRN",
    "HUARONG FINANCE 2017 CO LTD",
    "HRAMG 3.875 11/13/29 '29 MTN",
    "CCFAM 3.625 09/30/30 '30 MTN",
    "HUARONG FINANCE II CO LTD",
    "HUASING INTERNATIONAL HOLDINGS CO LTD",
    "HUATONG INTERNATIONAL INVESTMENT HOLDINGS CO LTD",
    "HUBEI SCIENCE & TECHNOLOGY INVESTMENT GROUP HONG KONG CO LTD",
    "Hopson Development Holdings Limited",
    "INDUSTRIAL AND COMMERCIAL BANK OF CHINA LTD (HONG KONG BRANCH)",
    "Industrial and Commercial Bank of China Lto",
    "JIAOZUO STATE OWNED CAPITAL OPERATION HOLDING GROUP CO LTD",
    "JIMO CITY INVESTMENT DEVELOPMENT CO LTD",
    "JINGZHOU CITY DEVELOPMENT HOLDING GROUP CO LTD",
    "JOY TREASURE ASSETS HOLDINGS INC",
    "Jiayuan International Group Ltd",
    "Longfor Group Holdings Limited",
    "MEGA WISDOM GLOBAL LTD",
    "MINGHU INTERNATIONAL (BVI) INVESTMENT DEVELOPMENT CO LTD",
    "Meituan",
    "NEW METRO GLOBAL LTD",
    "NWD FINANCE (BVI) LTD",
    "Nanyang Commercial Bank Limited",
    "Nomura Holdings, Inc.",
    "Powerlong Real Estate Holdings Limited",
    "QINGDAO JIAOZHOU BAY DEVELOPMENT CO LTD",
    "QUAN CHENG FINANCIAL HOLDINGS (BVI) LTD",
    "RAINMAKER SOLUTIONS",
    "Ronshine China Holdings Limited",
    "SDG FINANCE LTD",
    "SEPCO VIRGIN LTD",
    "SHAANXI FINANCIAL ASSETS MANAGEMENT CO LTD",
    "SHANDONG IRON AND STEEL XINHENG INTERNATIONAL COMPANY LTD",
    "SHANGRAO CITY CONSTRUCTION INVESTMENT AND DEVELOPMENT GROUP CO LTD",
    "SHUI ON DEVELOPMENT HOLDING LTD",
    "SHUIFA INTERNATIONAL HOLDINGS BVI CO LTD",
    "SND INTERNATIONAL (BVI) CO LTD",
    "SOAR WISE LTD",
    "SPIC PREFERRED COMPANY NO.5 LTD",
    "Seazen Group Ltd",
    "Shenzhen Expressway Corp Ltd",
    "Societe Generale SA",
    "Standard Chartered PLC",
    "Sunac China Holdings Limited",
    "TAIZHOU INFRASTRUCTURE CONSTRUCTION INVESTMENT CO LTD",
    "TFI OVERSEAS INVESTMENT LTD",
    "TIANQI FINCO CO LTD",
    "The Bank of East Asia, Limited",
    "Tianfeng Securities Co Ltd",
    "UBSG 6.875 Perp 6.875 '32 FRN",
    "UBSG 4.875 Perp '27 FRN",
    "UBSG 4.375 Perp '31FRN",
    "VANKE REAL ESTATE (HONG KONG) CO LTD",
    "WEIFANG URBAN CONSTRUCTION DEVELOPMENT INVESTMENT GROUP CO LTD",
    "WUHAN METRO GROUP CO LTD",
    "West China Cement Ltd",
    "Wynn Macau, Limited",
    "WYNNM 6.750 02/15/34'28 PUT - CIBHK",
    "WYNNM 5.625 08/26/28 '23 - CIBHK",
    "WYNNM 5.625 08/26/28 '23 - CISL",
    "WYNNM 6.750 02/15/34'28 PUT - CISL",
    "XIANJIN INDUSTRY INVESTMENT COMPANY LTD",
    "XINGYE GOLD HONG KONG MINING CO LTD",
    "Yuzhou Group Holdings Co Ltd",
    "ZHAOQING GUOLIAN INVESTMENT HOLDING CO LTD",
    "ZHEJIANG BARON (BVI) COMPANY LTD",
    "ZHEJIANG XINCHANG INVESTMENT DEVELOPMENT CO LTD",
    "ZHENGZHOU AIRPORT XIN GANG INVESTMENT & DEVELOPMENT CO LTD",
    "ZIBO HIGH TECH INTERNATIONAL INVESTMENT CO LTD",
    "Zhenro Properties Group Ltd"
]
]

# --- 侧边栏：上传文件 ---
st.sidebar.header("上传对账文件")
mapping_file = st.sidebar.file_uploader("上传映射表 (Apex Name & Enfusion Name.xlsx)", type=["xlsx"])
apex_file = st.sidebar.file_uploader("上传 Apex 报告 (Excel)", type=["xlsx", "xls"])

if mapping_file and apex_file:
    mapping_df = pd.read_excel(mapping_file)
    
    # 读取 Apex 文件
    df_apex = pd.read_excel(apex_file, skiprows=3)
    df_apex.columns = [str(c).strip() for c in df_apex.columns]
    name_col = [c for c in df_apex.columns if 'Quantity' in c or 'Identifier' in c or 'BOND' in c][0]
    amount_col = df_apex.columns[-1]
    apex_df = df_apex[[name_col, amount_col]].dropna()
    apex_df.columns = ['APEX_NAME', 'APEX_AMOUNT']
    apex_df['APEX_AMOUNT'] = pd.to_numeric(apex_df['APEX_AMOUNT'], errors='coerce')

    # --- 主界面：整列文本粘贴输入 ---
    st.subheader("📋 粘贴 Enfusion 的 Base Amount 序列")
    st.markdown("左侧是固定的债券名称列表，你只需要在下方文本框中**直接复制粘贴 Enfusion 那一整列金额**（支持换行、带有 `$` 或被截断换行的数字），系统会按顺序自动对齐！")

    # 默认给出一个模拟的带换行和美元符号的文本示例
    default_pasted_text = """$0.00
$0.00
$2,061.14
$0.00
$19,833.33
$0.00
$0.00
$38,000.00
$8,854.17
$0.00
$33,1
60.83"""

    pasted_text = st.text_area("在此处粘贴金额列 (Base Amount)", value=default_pasted_text, height=200)

    # --- 智能解析与清洗断行文本 ---
    def parse_amounts_text(text, expected_len):
        raw_lines = [line.strip() for line in text.split('\n') if line.strip()]
        amounts = []
        i = 0
        while i < len(raw_lines):
            curr = raw_lines[i]
            # 如果某一行没有以 '$' 开头且前面已有金额，说明它是上一行被截断的后半截（如 "60.83"）
            if not curr.startswith('$') and amounts:
                amounts[-1] += curr
            else:
                amounts.append(curr)
            i += 1
            
        # 转为 float
        parsed_vals = []
        for item in amounts:
            clean_str = item.replace('$', '').replace(',', '').strip()
            try:
                parsed_vals.append(float(clean_str))
            except ValueError:
                parsed_vals.append(0.0)
                
        # 补齐或截断到与标准列表长度一致
        if len(parsed_vals) < expected_len:
            parsed_vals.extend([0.0] * (expected_len - len(parsed_vals)))
        return parsed_vals[:expected_len]

    # 执行解析
    parsed_amounts = parse_amounts_text(pasted_text, len(DEFAULT_ENFUSION_ISSUERS))

    # 构造预览表格
    preview_df = pd.DataFrame({
        "ENFUSION_ISSUER": DEFAULT_ENFUSION_ISSUERS,
        "ENFUSION_AMOUNT": parsed_amounts
    })
    
    st.markdown("👀 **解析后的债券与金额对应预览：**")
    st.dataframe(preview_df, use_container_width=True, height=200)

    # --- 开始对账计算 ---
    if st.button("🚀 开始执行对账", type="primary"):
        enfusion_df = preview_df[preview_df['ENFUSION_AMOUNT'] != 0].copy()
        
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

        # 合并对账
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
        
        st.subheader("📊 对账结果看板")
        st.dataframe(result_df, use_container_width=True)
        
        # 下载按钮
        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 下载对账结果 CSV", data=csv, file_name="bond_reconciliation_result.csv", mime="text/csv")
else:
    st.warning("请先在左侧侧边栏上传【映射表】和【Apex 报告文件】。")

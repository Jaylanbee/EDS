import os
import pandas as pd
from src.analyzer import EDSAnalyzer
from src.adaptive_engine import AdaptiveEngine

def generate_decision_graph(data_path: str, output_path: str, available_hours: float = 2.0, target_mode: str = 'A++'):
    """Generates the text-based Application Layer Output (決勝圖譜)."""

    print(f"Initializing EDS Analyzer for data: {data_path}")
    analyzer = EDSAnalyzer(data_path)

    if analyzer.df.empty:
        print("Data is empty. Cannot generate graph.")
        return

    # Read personal dynamic data from RDQ
    adaptive_engine = AdaptiveEngine()
    modifiers = adaptive_engine.get_priority_modifiers()
    latest_weakness = adaptive_engine.get_latest_weakness_summary()

    # Run Decision Engine with personal modifiers
    print(f"Running Decision Engine (Target: {target_mode})...")
    roi_df = analyzer.module_d_priority_score(mode=target_mode, personal_modifiers=modifiers)
    trap_df = analyzer.module_b_trap_analysis()

    if roi_df.empty:
        print("Failed to calculate ROI. Exiting.")
        return

    # Pick subjects based on available hours
    selected_topics = []
    accumulated_hours = 0.0

    for _, row in roi_df.iterrows():
        est_time = row.get('預估補強時間', 2.0)
        if pd.isna(est_time): est_time = 2.0

        # We try to fit topics up to slightly over available hours
        if accumulated_hours < available_hours:
            selected_topics.append(row)
            accumulated_hours += est_time
        else:
            break

    # Output generation
    output_lines = []

    # Handoff greeting if RDQ data is present
    if latest_weakness:
        rdq_topic = latest_weakness.get('topic')
        rdq_reason = latest_weakness.get('reason', '觀念不夠熟練')
        output_lines.append(f"收到 RDQ 傳來的資料！我看到你在『{rdq_topic}』的「{rdq_reason}」上還有點卡關。")
        output_lines.append(f"距離實戰越來越近，我們今天先不念課本，直接來看歷屆會考最常考的題型，準備好了嗎？\n")

    output_lines.append(f"📅 今天（{available_hours} 小時）該讀：\n")

    for i, topic in enumerate(selected_topics):
        topic_code = topic['X軸主代碼']
        stars = topic['評等']
        output_lines.append(f"{(i+1):02d} {topic_code}    效益 {stars}")

    output_lines.append(f"\n⏱ 預估投入：{accumulated_hours:.1f} 小時")

    # Estimate score gain roughly (dummy logic for visual representation)
    score_gain_est = min(len(selected_topics) * 1.5, 5.0)
    output_lines.append(f"📈 預估提升：{score_gain_est:.1f} 分")

    # Extract weak point from traps if possible
    main_weakness = "無明顯弱點資料"
    if not trap_df.empty:
         common_reasons = trap_df['失分原因'].value_counts()
         if not common_reasons.empty:
             main_weakness = common_reasons.index[0]

    output_lines.append(f"🎯 主要改善方向：{main_weakness}")

    # Add a generic trap warning based on traps
    trap_warning = "請留意常見題型陷阱。"
    if not trap_df.empty:
        # Get the code with the lowest pass rate
        worst_trap = trap_df.iloc[0]
        trap_warning = f"複習 {worst_trap['X軸主代碼']} 時，留意「{worst_trap['失分原因']}」相關陷阱。"

    output_lines.append(f"⚠️ 常見陷阱：{trap_warning}")

    output_text = "\n".join(output_lines)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)

    print(f"\n=== 決勝圖譜 (Decision Graph) ===")
    print(output_text)
    print(f"=================================")
    print(f"\nOutput saved to {output_path}")

if __name__ == "__main__":
    # Ensure outputs directory exists
    os.makedirs('outputs', exist_ok=True)
    generate_decision_graph('exam-data/tagging_template.csv', 'outputs/daily_suggestion.txt')

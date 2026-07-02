
from datetime import datetime

from database import Database

import logging
logger = logging.getLogger(__name__)

def get_stats(records: list[dict[str, any]]) -> dict[str, any] | None:
    total = len(records)
   
    if total == 0:
        return None

    correct = sum(1 for r in records if r["grade"] == "Correct")
    partial = sum(1 for r in records if r["grade"] == "Partially Correct")
    incorrect = sum(1 for r in records if r["grade"] == "Incorrect")
    fully_correct_percent = correct / total
    partial_and_correct_percent = (correct + partial) / total
    total_weighted_score = sum(r["score"] for r in records)
    weighted_average = total_weighted_score / total
    
    return {
        "total": total,
        "correct": correct,
        "partial": partial,
        "incorrect": incorrect,
        "correct%": fully_correct_percent,
        "partial%": partial_and_correct_percent,
        "weighted": weighted_average
            }

def score_bar(score: float, width: int = 10) -> str:
    filled = int(score * width)
    empty = width - filled
    return "[" + "█" * filled + "░" * empty + "]"

def get_trend(records: list[dict[str, any]]) -> str:
    records_sorted = sorted(records, key=lambda r: r["date"])
    
    if len (records_sorted) < 2:
        return "Needs more data"
    mid = int(len(records_sorted) / 2)

    first_half = records_sorted[:mid]
    second_half = records_sorted[mid:]

    first_average = (sum(r["score"] for r in first_half)) / len(first_half)
    second_average = (sum(r["score"] for r in second_half)) / len(second_half)
    
    if first_average < second_average:
        return "Improvement ↑"
    elif first_average > second_average:
        return "Worsen ↓"
    else:
        return "No Change →"

def generate_report(topic_groups: dict[str, any]) -> str:
    topic_with_stats = []
    for topic, records in topic_groups.items():
        date_groups = {}
        averages = []
        stats = get_stats(records)
        for record in records:
            if record["date"] not in date_groups:
                date_groups[record["date"]] = []
            date_groups[record["date"]].append(record["score"])
        for date, scores in date_groups.items():
            avg = sum(scores) / len(scores)
            averages.append({"date": date, "score": avg})
        if stats is not None:
            topic_with_stats.append((topic, records, stats, averages))

    

    topic_with_stats.sort(key=lambda x: x[2]['weighted'])
    
    lines = []
    lines.append("Weakness Ranking")
    lines.append("=" * 50)

    for topic, records, stats, averages in topic_with_stats:
        trend = get_trend(records)
        lines.append("  ")
        lines.append(topic)
        lines.append(f"Total: {stats['total']} | Correct: {stats['correct']} | Partially Correct: {stats['partial']} | Incorrect: {stats['incorrect']} |")
        lines.append(f" Percentage Correct: {stats['correct%']:.0%} | Percentage Correct or Partially Correct: {stats['partial%']:.0%} | Weighted Average: {stats['weighted']:.2f}")
        lines.append(f"  Trend: {trend}")
        lines.append("  History:")

        for entry in sorted(averages, key = lambda r: r["date"], reverse = True):
            bar = score_bar(entry["score"])
            if entry["score"] >= .8:
                g = "Correct"
            elif .8 > entry["score"] >= .4:
                g = "Partially Correct"
            else:
                g = "Incorrect"
            lines.append(f"     {entry['date']}: {bar} {entry['score']:.1f}  {g}")
    return "\n".join(lines)

def run_analytics(db: Database) -> None:
  
    today = datetime.now().strftime("%Y-%m-%d-%I-%M-%p")

    topic_groups = {}

    rows = db.fetch_topic_grades()

    if not rows:
        print("No data found. Grade a session first to proceed.")
        exit()

    for row in rows:
        date = row[0]
        topic = row[1]
        grade = row[2]

        if grade == "Correct":
            score = 1.0
        elif grade == "Partially Correct":
            score = .5
        else:
            score = 0.0
        
        if topic not in topic_groups:
            topic_groups[topic] = []
        topic_groups[topic].append({
                "date": date,
                "grade": grade,
                "score": score
        })


    report = generate_report(topic_groups)

    if report is None:
        print("Analytics report failed to generate. Please retry.")
        exit()

    with open(f"analytics report {today}.txt", "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Analytics saved to 'analytics report {today}.txt'")

if __name__ == "__main__":
    run_analytics()
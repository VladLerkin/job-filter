"""Точка входа CLI: python -m job_filter"""
from job_filter.services.pipeline import fetch_and_filter_jobs

if __name__ == "__main__":
    matched = fetch_and_filter_jobs()
    print(f"\n🎯 Итого вакансий в сухом остатке (Score >= 50): {len(matched)}\n")
    for job in matched:
        print(f"🔥 [{job.get('score')}/100 | {job.get('tier')}] {job['title']} @ {job['company']} ({job['date_posted']})")
        print(f"🔗 {job['url']}\n")

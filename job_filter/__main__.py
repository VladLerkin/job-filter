"""Точка входа CLI: python -m job_filter [rescore [--diff]]"""
import sys

from job_filter import config
from job_filter.db.connection import db_session
from job_filter.services.pipeline import fetch_and_filter_jobs
from job_filter.services.skills_service import preview_rescore_diff, rescore_all_jobs


def _run_rescore_cli(dry_run: bool) -> None:
    with db_session() as conn:
        diff = preview_rescore_diff(conn)
        promoted = diff["promoted_to_matched"]
        demoted = diff["demoted_to_rejected"]
        other = diff["other_changes"]
        print(
            f"📊 Проверено обогащённых вакансий: {diff['total_evaluated']} | "
            f"⬆️ В выдачу: {len(promoted)} | ⬇️ В отсев: {len(demoted)} | "
            f"🔄 Изменился скор/тир: {len(other)}"
        )
        for item in promoted:
            print(
                f"  ⬆️ [{item['job_id']}] {item['title']} @ {item['company']}: "
                f"{item['old_score']} ({item['old_reject_reason']}) -> {item['new_score']} ({item['new_tier']})"
            )
        for item in demoted:
            print(
                f"  ⬇️ [{item['job_id']}] {item['title']} @ {item['company']}: "
                f"{item['old_score']} ({item['old_tier']}) -> {item['new_score']} ({item['new_reject_reason']})"
            )
        if not dry_run:
            updated = rescore_all_jobs(conn)
            print(f"✅ Обновлено записей в БД: {updated}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "rescore":
        _run_rescore_cli(dry_run=("--diff" in args or "--dry-run" in args))
    else:
        matched = fetch_and_filter_jobs()
        print(f"\n🎯 Итого вакансий в сухом остатке (Score >= {config.FAIR_SCORE_THRESHOLD}): {len(matched)}\n")
        for job in matched:
            print(f"🔥 [{job.get('score')}/100 | {job.get('tier')}] {job['title']} @ {job['company']} ({job['date_posted']})")
            print(f"🔗 {job['url']}\n")


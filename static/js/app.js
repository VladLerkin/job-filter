    let currentTab = 'top';
    let pollTimer = null;
    let logCursor = 0;
    let currentLang = localStorage.getItem('job_filter_lang') || 'en';

    const I18N = {
      en: {
        app_subtitle: "Candidate: Vladislav Yarygin • AI Agentic & Senior Backend (Java, Kotlin, Python) • Remote / B2B",
        search_terms_label: "Search Terms (comma-separated)",
        location_label: "Location / Region",
        hours_label: "Hours Old",
        llm_limit_label: "AI Limit",
        easy_apply_label: "⚡ Easy Apply",
        easy_apply_title: "Filter jobs with quick Easy Apply",
        btn_run_full: "🚀 Search + AI Filter",
        btn_run_enrich: "🧠 AI Only",
        btn_run_enrich_title: "Enrich already scraped jobs in DB via agy CLI without new scraping",
        source_label: "🌐 Source (select one):",
        pipeline_running: "Pipeline running...",
        pipeline_finished: "Pipeline finished",
        hide_log: "Hide Log",
        show_log: "Show Log",
        clear_log: "Clear",
        tab_top_text: "Top Match ≥70",
        tab_good_text: "Good 60–69",
        tab_fair_text: "Fair 50–59",
        tab_pending_text: "Pending AI",
        tab_applied_text: "Applied",
        tab_rejected_text: "Dismissed",
        tab_blacklist_text: "Blacklist",
        tab_skills_text: "Skills & Scoring",
        tab_candidate: "👤 Profile & CV",
        btn_rescore_all: "🔄 Rescore Jobs",
        total_in_db: "Total in DB:",
        blacklist_title: "💩 Job Boards & ATS Blacklist",
        blacklist_badge: "Double Redirect LinkedIn → ATS",
        blacklist_desc: "Synchronized with job-auto-applier extension. Navigating to a banned domain displays a warning and binds the employer to this board.",
        last_opened_label: "🔗 Last opened vacancy:",
        last_opened_none: "Not opened yet in this session",
        btn_ban_last_opened: "⛔ Add last opened to Blacklist",
        bad_domain_label: "Domain or full URL of job board (e.g. cims.com or redirect link)",
        bad_domain_placeholder: "cims.com or https://careers-company.icims.com/...",
        btn_clipboard: "📋 From Clipboard",
        bad_reason_label: "Reason (why inaccessible)",
        bad_reason_default: "Impossible to fill form (in blacklist)",
        btn_add_blacklist: "➕ Add to Blacklist",
        banned_domains_title: "🚫 Banned Job Board / ATS Domains",
        banned_companies_title: "🏢 Companies with problematic ATS/boards",
        candidate_title: "👤 Candidate Data in Database",
        candidate_desc: "Used by AI when evaluating resume_fit. Compatible with job-auto-applier format.",
        btn_upload_pdf: "📄 Upload PDF Resume",
        btn_export_json: "⬇️ Export JSON",
        btn_import_json: "⬆️ Import JSON",
        btn_save_db: "💾 Save to DB",
        profile_label: "Your Profile / Preferences (Location, Visa / B2B, Salary expectations):",
        profile_placeholder: "E.g., Number of years of experience, address, salary expectations, Work Authorization note...",
        cv_label: "Your CV / Resume Text (Full structured resume for skills matching):",
        cv_placeholder: "Paste your structured CV / Resume text here...",
        matrix_title: "🎯 Skills Matrix & Scoring Categories",
        matrix_desc: "Define experience in years for each skill. Vacancy score points are calculated via: points = min(years × multiplier, category limit) or adjusted manually.",
        btn_import_cv_skills: "📄 Import from PDF Resume",
        btn_add_category: "➕ Add Category",
        btn_add_skill: "➕ Add Skill",
        btn_reset_defaults: "↺ Reset to Defaults",
        btn_rescore_vacancies: "🔄 Rescore Vacancies",
        modal_blacklist_title: "⛔ Add to Blacklist (Problematic Form)",
        modal_quick_select: "Quick Platform Select (1-click):",
        modal_only_company: "🏢 Only this company",
        modal_url_label: "URL or Domain of Job Board (where redirected):",
        modal_url_placeholder: "E.g. cims.com or paste from browser",
        modal_url_hint: "If left blank, the company itself will be blacklisted and all its future jobs flagged.",
        btn_cancel: "Cancel",
        btn_confirm_blacklist: "⛔ Blacklist and Dismiss",
        modal_cat_title: "Skill Category",
        modal_cat_id_label: "Category ID (slug, e.g. ai_agentic):",
        modal_cat_name_label: "Category Title (with emoji):",
        modal_cat_mult_label: "Multiplier (per 1 year):",
        modal_cat_mult_hint: "Negative for penalty deductions",
        modal_cat_max_label: "Max Points (cap):",
        modal_cat_max_hint: "Category cap in scoring",
        modal_cat_sort_label: "Sort Order (number):",
        btn_save_category: "💾 Save Category",
        modal_skill_title: "Candidate Skill",
        modal_skill_cat_label: "Category:",
        modal_skill_id_label: "Skill ID (slug, e.g. langgraph):",
        modal_skill_name_label: "Skill Name:",
        modal_skill_years_label: "Experience (years):",
        modal_skill_points_label: "Scoring Points:",
        modal_skill_primary_label: "⭐ Primary Skill",
        modal_skill_aliases_label: "Synonyms / Aliases (comma-separated):",
        btn_save_skill: "💾 Save Skill",
        modal_cv_title: "📄 AI Resume Analysis & Skills Matrix",
        modal_cv_desc: "AI extracted structured resume text and calculated experience for each skill. Review and select changes to apply.",
        modal_cv_summary_title: "Candidate Profile Summary:",
        tab_cv_skills_text: "Skills & Experience",
        tab_cv_text: "📄 Structured Resume Text",
        badge_cv_new_label: "New:",
        badge_cv_updated_label: "Updated:",
        badge_cv_unchanged_label: "Unchanged:",
        badge_cv_new: "New",
        badge_cv_updated: "Updated",
        badge_cv_unchanged: "Unchanged",
        col_status: "Status",
        col_skill_cat: "Skill & Category",
        col_experience: "Experience (yrs)",
        col_points: "Score Points",
        col_primary: "Primary",
        col_aliases: "Aliases",
        opt_update_cv: "📝 Update resume text in DB (cv_text)",
        opt_update_skills: "🎯 Apply selected skills to scoring matrix",
        opt_update_profile: "👤 Add summary to candidate preferences",
        opt_rescore_all: "🔄 Rescore all vacancies immediately",
        btn_apply_cv: "✅ Apply Selected Changes",
        loading_cv_title: "AI is Analyzing Resume",
        loading_cv_desc: "Extracting text from PDF, parsing career timeline, and evaluating skill experience...",
        btn_open_job: "🔗 Open Vacancy ↗",
        btn_open_job_bad: "⚠️ Open (Blacklisted) ↗",
        btn_applied_done: "✅ Applied",
        btn_not_fit: "❌ Not a fit",
        btn_not_fit_title: "Mark as not suitable and specify reason for AI learning",
        modal_reject_title: "❌ Why is this job not a fit?",
        modal_reject_quick_select: "Quick reason select (1-click):",
        modal_reject_reason_label: "Reason (will be saved for future AI learning):",
        modal_reject_placeholder: "Specify details or select an option above...",
        btn_confirm_reject: "❌ Save & Dismiss",
        user_reject_reason_label: "Dismissed reason",
        btn_edit_reason: "Edit",
        btn_return_new: "↩ Return to New",
        btn_blacklist_job: "⛔ Blacklist",
        btn_hide_job: "Dismiss",
        btn_hide_immediate: "🗑️ Dismiss Immediately",
        fit_summary_label: "💡 Resume Fit:",
        cat_multiplier_label: "Multiplier:",
        cat_limit_label: "Cap:",
        cat_skills_count_label: "Skills:",
        btn_edit: "✏️ Edit",
        empty_category_notice: "No skills in this category yet. Click «➕ Add Skill».",
        empty_categories_notice: "No categories found. Click «➕ Add Category» to create one.",
        toast_saved: "Profile saved successfully",
        toast_reset: "Default categories and skills restored",
        toast_applied: "Marked as Applied ✅",
        toast_rejected: "Marked as not suitable ❌",
        toast_status_updated: "Status updated",
        filter_rejected_scope: "Filter view:",
        subtab_all_rejected: "All Dismissed",
        subtab_user_rejected: "👤 Dismissed by Me",
        subtab_auto_rejected: "🤖 Filtered by Auto/AI",
        subtab_reasons_title: "📋 Reasons why you dismissed:",
        subtab_categories_title: "🤖 Auto-filter categories:",
        click_to_filter_hint: "Click to filter list",
        all_reasons_chip: "All Reasons",
        all_categories_chip: "All Categories",
        user_hidden_reason: "Hidden to trash",
        btn_restore_to_feed: "↩ Restore to Feed",
        toast_job_restored: "Job restored to list! ⭐",
        cat_location: "📍 Country / Location",
        cat_low_score: "🎯 Low AI Score (<50)",
        cat_missing_keywords: "🔍 Missing Keywords",
        cat_excluded_title: "🚫 Excluded Title",
        cat_seniority: "👶 Seniority Mismatch",
        cat_language: "🗣️ Language Requirement",
        cat_industry: "🏢 Staffing / Agency",
        cat_bad_board: "⛔ Blacklisted ATS",
        cat_contract: "📄 Contract Lock",
        cat_other: "⚙️ Other Filters",
        cat_unmatched: "❓ Search Mismatch",
        applied_funnel_label: "Application Funnel:",
        applied_stage_all: "All Applied",
        applied_stage_waiting: "Waiting Reply",
        applied_stage_confirmed: "Confirmed",
        applied_stage_interview: "HR / Interview",
        applied_stage_rejected: "Company Rejected",
        btn_copy_tracker_prompt: "Prompt for @job-application-tracker",
        btn_sync_tracker: "Sync with @job-application-tracker",
        applied_company_reasons_title: "📋 Company Rejection Reasons (from emails):",
        modal_tracker_title: "Sync Applications with @job-application-tracker",
        modal_tracker_desc: "Query @job-application-tracker directly via agy CLI or paste its report from Web Gemini — AI will match companies and mark confirmations, rejections with reasons, and interview invites.",
        modal_tracker_step1: "Query for @job-application-tracker (with your Applied companies):",
        btn_copy_prompt: "Copy Prompt for Gemini",
        btn_run_direct_agy: "Query Directly via agy CLI",
        modal_tracker_show_prompt: "Show prompt text with companies list",
        modal_tracker_step2: "Or paste the response from @job-application-tracker here (text, table, list):",
        modal_tracker_placeholder: "Paste output from @job-application-tracker (e.g. list of companies with confirmations, rejections + reasons, or HR screening invites)...",
        btn_parse_and_mark: "Parse with AI & Mark Vacancies",
        modal_company_stage_title: "📬 Company Response Status",
        modal_company_stage_select_label: "Application Stage:",
        modal_company_reason_label: "Company rejection reason or interview details:",
        btn_run_macro: "⚡ Auto-All",
        btn_run_macro_title: "Automatically iterate through all enabled job systems using last check time",
        btn_macro_settings_title: "Configure Multi-System Macro Pipeline",
        btn_stop_pipeline: "⏹️ Stop",
        modal_macro_title: "Multi-System Auto-Run (Macro Pipeline)",
        modal_macro_desc: "Iterates through enabled job boards in order, calculates Hours Old from each system's last check time, and deduplicates vacancies by Title + Company across boards.",
        macro_exec_mode_label: "1️⃣ Execution & AI Enrichment Strategy:",
        macro_mode_per_provider_title: "🔄 Per System Immediately (Recommended)",
        macro_mode_per_provider_desc: "System → Scrape → AI Enrich & Score → Next System. Top matches appear immediately after each board.",
        macro_mode_batch_title: "📦 Scrape All Cards First → AI Batch at End",
        macro_mode_batch_desc: "Quickly scrapes candidate cards from all enabled systems into Pending AI, then runs one combined AI enrichment pass.",
        macro_hours_mode_label: "2️⃣ Search Depth (Hours Old) & Limits:",
        macro_hours_auto_title: "🕒 Auto from Last Check (+1h buffer)",
        macro_hours_auto_desc: "Uses elapsed time since each system's previous check + 1 hour so nothing is missed or re-scraped.",
        macro_hours_fixed_title: "📌 Fixed Hours for All Systems",
        macro_hours_fixed_desc: "Always use the Default Hours Old value for every system regardless of last check timestamp.",
        macro_default_hours_label: "Default Hours (1st run):",
        macro_max_auto_hours_label: "Max Auto Hours (cap):",
        macro_results_wanted_label: "Cards Limit / Step:",
        macro_llm_limit_label: "AI Enrich Limit:",
        macro_steps_label: "3️⃣ Systems & Locations Queue:",
        macro_steps_hint: "Toggle job boards and select one or more locations/countries per system",
        btn_macro_save: "Save Settings",
        btn_macro_save_and_run: "Save & Run Macro"
      },
      ru: {
        app_subtitle: "Кандидат: Владислав Ярыгин • AI Agentic & Senior Backend (Java, Kotlin, Python) • Удалёнка из Грузии (B2B)",
        search_terms_label: "Поисковые запросы (через запятую)",
        location_label: "Локация / Регион",
        hours_label: "Часов",
        llm_limit_label: "Лимит ИИ",
        easy_apply_label: "⚡ Easy Apply",
        easy_apply_title: "Искать только вакансии с быстрым откликом Easy Apply",
        btn_run_full: "🚀 Собрать + ИИ-фильтр",
        btn_run_enrich: "🧠 Только ИИ",
        btn_run_enrich_title: "Обогатить через agy CLI уже скачанные в БД вакансии без нового парсинга",
        source_label: "🌐 Источник (выбери один):",
        pipeline_running: "Выполняется пайплайн...",
        pipeline_finished: "Пайплайн завершен",
        hide_log: "Скрыть лог",
        show_log: "Показать лог",
        clear_log: "Очистить",
        tab_top_text: "Топ ≥70",
        tab_good_text: "Хорошие 60–69",
        tab_fair_text: "Проходные 50–59",
        tab_pending_text: "Ждут ИИ",
        tab_applied_text: "Откликнулся",
        tab_rejected_text: "Отсеянные",
        tab_blacklist_text: "Чёрный список",
        tab_skills_text: "Навыки и Скоринг",
        tab_candidate: "👤 Профиль и CV",
        btn_rescore_all: "🔄 Пересчитать скоринг",
        total_in_db: "Всего в БД:",
        blacklist_title: "💩 Чёрный список джоб-бордов и ATS",
        blacklist_badge: "Двойной переход LinkedIn → ATS",
        blacklist_desc: "Синхронизировано с расширением job-auto-applier. При переходе на забаненный домен всплывает предупреждение, а компания привязывается к этому борду.",
        last_opened_label: "🔗 Последняя открытая вакансия:",
        last_opened_none: "Пока не открывалась в этой сессии",
        btn_ban_last_opened: "⛔ Добавить последнюю открытую в черный список",
        bad_domain_label: "Домен или полный URL джоб-борда (например, cims.com или ссылка с редиректа)",
        bad_domain_placeholder: "cims.com или https://careers-company.icims.com/...",
        btn_clipboard: "📋 Из буфера",
        bad_reason_label: "Причина (почему не заполняется)",
        bad_reason_default: "Невозможно заполнить форму (в чёрном списке)",
        btn_add_blacklist: "➕ В чёрный список",
        banned_domains_title: "🚫 Забаненные домены джоб-бордов / ATS",
        banned_companies_title: "🏢 Компании с проблемными ATS/бордами",
        candidate_title: "👤 Данные кандидата в базе",
        candidate_desc: "Используется ИИ при оценке resume_fit. Совместимо с форматом экспорта/импорта job-auto-applier.",
        btn_upload_pdf: "📄 Загрузить PDF резюме",
        btn_export_json: "⬇️ Экспорт JSON",
        btn_import_json: "⬆️ Импорт JSON",
        btn_save_db: "💾 Сохранить в БД",
        profile_label: "Your Profile / Preferences (Предпочтения, локация, виза / B2B, зарплатные ожидания):",
        profile_placeholder: "E.g., Number of years of experience, address, salary expectations, Work Authorization note...",
        cv_label: "Your CV / Resume Text (Полный текст резюме для сопоставления навыков):",
        cv_placeholder: "Paste your structured CV / Resume text here...",
        matrix_title: "🎯 Матрица навыков и категории скоринга",
        matrix_desc: "Задавайте опыт в годах для каждого навыка. Баллы в скоринге вакансий рассчитываются по формуле: баллы = min(годы × множитель, лимит категории) или настраиваются вручную.",
        btn_import_cv_skills: "📄 Импорт из PDF резюме",
        btn_add_category: "➕ Добавить категорию",
        btn_add_skill: "➕ Добавить навык",
        btn_reset_defaults: "↺ Сбросить к базовым",
        btn_rescore_vacancies: "🔄 Пересчитать скоринг вакансий",
        modal_blacklist_title: "⛔ Добавить в чёрный список (проблемная форма)",
        modal_quick_select: "Быстрый выбор платформы (1 клик):",
        modal_only_company: "🏢 Только эту компанию",
        modal_url_label: "URL или домен джоб-борда (куда перекинуло после LinkedIn):",
        modal_url_placeholder: "Например: cims.com или вставь URL из браузера",
        modal_url_hint: "Если оставить пустым — в чёрный список занесётся сама компания, и все её будущие вакансии будут помечены.",
        btn_cancel: "Отмена",
        btn_confirm_blacklist: "⛔ Занести в чёрный список и скрыть",
        modal_cat_title: "Категория навыков",
        modal_cat_id_label: "ID категории (латиницей, например ai_agentic):",
        modal_cat_name_label: "Название категории (с эмодзи):",
        modal_cat_mult_label: "Множитель (за 1 год):",
        modal_cat_mult_hint: "Отрицательный для штрафов",
        modal_cat_max_label: "Максимум баллов (лимит):",
        modal_cat_max_hint: "Потолок категории в скоринге",
        modal_cat_sort_label: "Порядок сортировки (число):",
        btn_save_category: "💾 Сохранить категорию",
        modal_skill_title: "Навык кандидата",
        modal_skill_cat_label: "Категория:",
        modal_skill_id_label: "ID навыка (латиницей):",
        modal_skill_name_label: "Название навыка:",
        modal_skill_years_label: "Опыт (в годах):",
        modal_skill_points_label: "Баллы в скоринге:",
        modal_skill_primary_label: "⭐ Ключевой навык (Primary)",
        modal_skill_aliases_label: "Синонимы / алиасы (через запятую):",
        btn_save_skill: "💾 Сохранить навык",
        modal_cv_title: "📄 ИИ-разбор резюме и матрица навыков",
        modal_cv_desc: "ИИ извлек структурированный текст резюме и рассчитал стаж по каждому навыку. Выберите, какие изменения применить в базе.",
        modal_cv_summary_title: "Резюме профиля кандидата:",
        tab_cv_skills_text: "Навыки и стаж",
        tab_cv_text: "📄 Структурированный текст резюме",
        badge_cv_new_label: "Новых:",
        badge_cv_updated_label: "Обновленных:",
        badge_cv_unchanged_label: "Без изменений:",
        badge_cv_new: "Новый",
        badge_cv_updated: "Изменился",
        badge_cv_unchanged: "Без изм.",
        col_status: "Статус",
        col_skill_cat: "Навык & Категория",
        col_experience: "Стаж (годы)",
        col_points: "Баллы скоринга",
        col_primary: "Primary",
        col_aliases: "Алиасы",
        opt_update_cv: "📝 Обновить текст резюме в базе (cv_text)",
        opt_update_skills: "🎯 Применить отмеченные навыки в матрицу скоринга",
        opt_update_profile: "👤 Добавить summary в предпочтения кандидата",
        opt_rescore_all: "🔄 Пересчитать скоринг всех вакансий сразу",
        btn_apply_cv: "✅ Применить выбранные изменения",
        loading_cv_title: "ИИ анализирует резюме",
        loading_cv_desc: "Извлекаем текст из PDF, восстанавливаем структуру карьеры и оцениваем стаж по навыкам...",
        btn_open_job: "🔗 Открыть вакансию ↗",
        btn_open_job_bad: "⚠️ Открыть (В чёрном списке) ↗",
        btn_applied_done: "✅ Откликнулся",
        btn_not_fit: "❌ Не подошла",
        btn_not_fit_title: "Отметить как не подходящую и указать причину для обучения ИИ",
        modal_reject_title: "❌ Почему вакансия не подошла?",
        modal_reject_quick_select: "Быстрый выбор типовой причины:",
        modal_reject_reason_label: "Причина (будет сохранена для последующего обучения):",
        modal_reject_placeholder: "Укажите подробности или выберите вариант выше...",
        btn_confirm_reject: "❌ Сохранить и скрыть",
        user_reject_reason_label: "Причина отклонения",
        btn_edit_reason: "Изменить",
        btn_return_new: "↩ Вернуть в новые",
        btn_blacklist_job: "⛔ В черный список",
        btn_hide_job: "Скрыть",
        btn_hide_immediate: "🗑️ Скрыть сразу",
        fit_summary_label: "💡 Резюме-фит:",
        cat_multiplier_label: "Множитель:",
        cat_limit_label: "Лимит:",
        cat_skills_count_label: "Навыков:",
        btn_edit: "✏️ Изменить",
        empty_category_notice: "В этой категории пока нет навыков. Нажмите «➕ Добавить навык».",
        empty_categories_notice: "Категории не найдены. Нажмите «➕ Добавить категорию», чтобы создать первую.",
        toast_saved: "Профиль успешно сохранен",
        toast_reset: "Базовый набор категорий и навыков восстановлен",
        toast_applied: "Отмечено как «Откликнулся» ✅",
        toast_rejected: "Отмечено как «Не подошла» ❌",
        toast_status_updated: "Статус обновлен",
        filter_rejected_scope: "Срез отсева:",
        subtab_all_rejected: "Все отсеянные",
        subtab_user_rejected: "👤 Отклонил я",
        subtab_auto_rejected: "🤖 Отсеяно автоматом",
        subtab_reasons_title: "📋 Причины, почему вы отказали:",
        subtab_categories_title: "🤖 Категории авто-отсева системой:",
        click_to_filter_hint: "Кликните по причине для фильтрации",
        all_reasons_chip: "Все причины",
        all_categories_chip: "Все категории",
        user_hidden_reason: "Скрыто в корзину",
        btn_restore_to_feed: "↩ Восстановить в поток",
        toast_job_restored: "Вакансия возвращена в список! ⭐",
        cat_location: "📍 Локация / Страна",
        cat_low_score: "🎯 Низкий скор ИИ (<50)",
        cat_missing_keywords: "🔍 Не хватает ключевых слов",
        cat_excluded_title: "🚫 Неподходящий тайтл",
        cat_seniority: "👶 Неподходящий грейд",
        cat_language: "🗣️ Языковые требования",
        cat_industry: "🏢 Отрасль / Рекрутинг",
        cat_bad_board: "⛔ Чёрный список ATS",
        cat_contract: "📄 Формат контракта",
        cat_other: "⚙️ Прочие фильтры",
        cat_unmatched: "❓ Не соответствует поиску",
        applied_funnel_label: "Воронка откликов:",
        applied_stage_all: "Все отклики",
        applied_stage_waiting: "Ждём ответа",
        applied_stage_confirmed: "Подтверждено",
        applied_stage_interview: "HR / Интервью",
        applied_stage_rejected: "Отказ компании",
        btn_copy_tracker_prompt: "Промпт для @job-application-tracker",
        btn_sync_tracker: "Синхронизировать с @job-application-tracker",
        applied_company_reasons_title: "📋 Причины отказов от компаний (из писем):",
        modal_tracker_title: "Синхронизация откликов с @job-application-tracker",
        modal_tracker_desc: "Опросите скилл @job-application-tracker напрямую через agy CLI или вставьте его отчёт из веб-Gemini — ИИ сопоставит компании и проставит подтверждения, отказы с причинами и приглашения на интервью.",
        modal_tracker_step1: "Запрос к скиллу @job-application-tracker (со списком ваших Applied-компаний):",
        btn_copy_prompt: "Скопировать запрос для Gemini",
        btn_run_direct_agy: "Опросить напрямую через agy CLI",
        modal_tracker_show_prompt: "Показать текст промпта со списком компаний",
        modal_tracker_step2: "Или вставьте сюда ответ от @job-application-tracker из Gemini (текст, таблица, список):",
        modal_tracker_placeholder: "Вставьте ответ от @job-application-tracker (например, список компаний с подтверждениями, отказами и причинами или приглашениями на HR-скрининг)...",
        btn_parse_and_mark: "Разобрать через ИИ и отметить вакансии",
        modal_company_stage_title: "📬 Статус ответа компании",
        modal_company_stage_select_label: "Этап отклика:",
        modal_company_reason_label: "Причина отказа компании или детали приглашения на интервью:",
        btn_run_macro: "⚡ Авто-обход",
        btn_run_macro_title: "Автоматически обойти все включенные системы по очереди с учётом времени последней проверки",
        btn_macro_settings_title: "Настройки макроса авто-обхода систем",
        btn_stop_pipeline: "⏹️ Стоп",
        modal_macro_title: "Авто-обход всех систем (Макрос)",
        modal_macro_desc: "Автоматически обходит выбранные площадки по очереди, рассчитывает глубину поиска (Hours Old) с момента последней проверки каждой системы и дедуплицирует вакансии по паре «Название + Компания» между бордами.",
        macro_exec_mode_label: "1️⃣ Стратегия обхода и ИИ-распознавания:",
        macro_mode_per_provider_title: "🔄 По каждой системе сразу (Рекомендуется)",
        macro_mode_per_provider_desc: "Система → Сбор карточек → ИИ-разбор и скоринг → Следующая система. Новые Топ-вакансии появляются в списке сразу после каждого борда.",
        macro_mode_batch_title: "📦 Сначала собрать все карточки → затем ИИ",
        macro_mode_batch_desc: "Быстро собирает карточки со всех включенных систем в «Ждут ИИ», а в конце запускает единый общий проход ИИ-обогащения и скоринга.",
        macro_hours_mode_label: "2️⃣ Глубина поиска (Hours Old) и лимиты:",
        macro_hours_auto_title: "🕒 Автоматически от последней проверки (+1ч запас)",
        macro_hours_auto_desc: "Для каждой системы берет время с её прошлого запуска + 1 час, чтобы ничего не пропустить и не парсить лишнее.",
        macro_hours_fixed_title: "📌 Фиксированное число часов для всех",
        macro_hours_fixed_desc: "Использовать одинаковое значение «Часов по умолчанию» для всех систем независимо от времени прошлой проверки.",
        macro_default_hours_label: "Часов по умолч. (1-й запуск):",
        macro_max_auto_hours_label: "Макс. авто-часов (потолок):",
        macro_results_wanted_label: "Лимит карточек / шаг:",
        macro_llm_limit_label: "Лимит ИИ-разбора:",
        macro_steps_label: "3️⃣ Системы и локации для поочередного обхода:",
        macro_steps_hint: "Отметьте площадки и одну или несколько стран/регионов",
        btn_macro_save: "Сохранить настройки",
        btn_macro_save_and_run: "Сохранить и запустить обход"
      }
    };

    function t(key) {
      if (I18N[currentLang] && I18N[currentLang][key] !== undefined) {
        return I18N[currentLang][key];
      }
      if (I18N.en && I18N.en[key] !== undefined) {
        return I18N.en[key];
      }
      return key;
    }

    function applyLanguage() {
      document.documentElement.lang = currentLang;

      const btnEn = document.getElementById('langBtnEn');
      const btnRu = document.getElementById('langBtnRu');
      if (btnEn && btnRu) {
        if (currentLang === 'en') {
          btnEn.className = 'px-2.5 py-1 rounded-md transition text-white bg-indigo-600 font-bold';
          btnRu.className = 'px-2.5 py-1 rounded-md transition text-slate-400 hover:text-white font-medium';
        } else {
          btnRu.className = 'px-2.5 py-1 rounded-md transition text-white bg-indigo-600 font-bold';
          btnEn.className = 'px-2.5 py-1 rounded-md transition text-slate-400 hover:text-white font-medium';
        }
      }

      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = t(key);
        if (val) el.textContent = val;
      });

      document.querySelectorAll('[data-i18n-html]').forEach(el => {
        const key = el.getAttribute('data-i18n-html');
        const val = t(key);
        if (val) el.innerHTML = val;
      });

      document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const val = t(key);
        if (val) el.placeholder = val;
      });

      document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const val = t(key);
        if (val) el.title = val;
      });

      if (typeof updateTabsText === 'function') {
        updateTabsText();
      }

      if (typeof updateLogButtonState === 'function') {
        updateLogButtonState();
      }
      if (typeof renderProviderCheckBadges === 'function') {
        renderProviderCheckBadges();
      }

      if (currentTab === 'skills' && typeof renderSkillsMatrix === 'function' && cachedSkillsMatrix && cachedSkillsMatrix.categories) {
        renderSkillsMatrix(cachedSkillsMatrix);
      } else if (currentTab !== 'candidate' && currentTab !== 'blacklist') {
        if (typeof renderJobsList === 'function' && cachedJobs && cachedJobs.length > 0) {
          renderJobsList();
        }
      }
    }

    function setLanguage(lang) {
      currentLang = (lang === 'ru') ? 'ru' : 'en';
      localStorage.setItem('job_filter_lang', currentLang);
      applyLanguage();
    }

    const SNIPPETS = {
      workAuth: "I am legally authorized to work from Georgia (country) and do not require visa sponsorship. I am seeking remote-only roles (e.g., via B2B contract, independent contractor, or Employer of Record/EOR) and do not require work authorization in the employer’s country (such as the US).",
      usAuthNote: "No, but I am seeking remote engagement from Georgia (country) as an independent contractor / B2B, which does not require US/local work authorization or visa sponsorship.",
      linkedin: "https://www.linkedin.com/in/iarygin-vladislav"
    };

    const PROVIDER_CONFIG = {
      linkedin: {
        label: "Охват поиска (LinkedIn)",
        remoteMechanism: "🌍 Единая мировая база • Макрорегионы Worldwide и EMEA ищут глобальную удалёнку одним запросом",
        hint: "LinkedIn: выберите Worldwide или EMEA для поиска глобальной удалёнки по всему миру или региону EMEA",
        supportsEasyApply: true,
        options: [
          { value: "EMEA", label: "🌍 EMEA (Европа, Ближний Восток, Африка)" },
          { value: "Worldwide", label: "🌐 Worldwide (Весь мир — глобальная удалёнка)" },
          { value: "European Union", label: "🇪🇺 European Union" },
          { value: "United Kingdom", label: "🇬🇧 United Kingdom" },
          { value: "Germany", label: "🇩🇪 Germany" },
          { value: "Netherlands", label: "🇳🇱 Netherlands" },
          { value: "Poland", label: "🇵🇱 Poland" },
          { value: "Spain", label: "🇪🇸 Spain" },
          { value: "Ireland", label: "🇮🇪 Ireland" },
          { value: "Switzerland", label: "🇨🇭 Switzerland" },
          { value: "United Arab Emirates", label: "🇦🇪 United Arab Emirates" },
          { value: "United States", label: "🇺🇸 United States" }
        ]
      },
      indeed: {
        label: "Региональный сервер-витрина (Indeed)",
        remoteMechanism: "🌐 У Indeed нет единого мирового сайта — запрос идёт с фильтром 100% Remote по выбранному домену, а ИИ отбирает вакансии с удалёнкой из Грузии / EMEA / Worldwide",
        hint: "Indeed разбит на отдельные домены стран (uk.indeed.com, de.indeed.com). Выбирайте крупные англоязычные IT-хабы Европы, куда компании постят EMEA/Global Remote вакансии",
        supportsEasyApply: true,
        options: [
          { value: "uk", label: "🇬🇧 Витрина UK (uk.indeed.com • хаб EMEA)" },
          { value: "germany", label: "🇩🇪 Витрина Germany (de.indeed.com • хаб EU)" },
          { value: "netherlands", label: "🇳🇱 Витрина Netherlands (nl.indeed.com • хаб EU)" },
          { value: "poland", label: "🇵🇱 Витрина Poland (pl.indeed.com • хаб CEE)" },
          { value: "spain", label: "🇪🇸 Витрина Spain (es.indeed.com)" },
          { value: "france", label: "🇫🇷 Витрина France (fr.indeed.com)" },
          { value: "ireland", label: "🇮🇪 Витрина Ireland (ie.indeed.com • EU English)" },
          { value: "switzerland", label: "🇨🇭 Витрина Switzerland (ch.indeed.com)" },
          { value: "portugal", label: "🇵🇹 Витрина Portugal (pt.indeed.com)" },
          { value: "czech republic", label: "🇨🇿 Витрина Czechia (cz.indeed.com)" },
          { value: "united arab emirates", label: "🇦🇪 Витрина UAE (ae.indeed.com • MENA)" },
          { value: "usa", label: "🇺🇸 Витрина USA (www.indeed.com • US/Global)" },
          { value: "canada", label: "🇨🇦 Витрина Canada (ca.indeed.com)" }
        ]
      },
      glassdoor: {
        label: "Региональный сервер-витрина (Glassdoor)",
        remoteMechanism: "🌐 У Glassdoor отдельные домены по странам — включается фильтр Work From Home (100% Remote), а ИИ проверяет доступность из Грузии / EMEA / Worldwide",
        hint: "Glassdoor: выберите домен-витрину (например UK или Germany), внутри которого ищутся Remote-вакансии",
        supportsEasyApply: true,
        options: [
          { value: "uk", label: "🇬🇧 Витрина UK (glassdoor.co.uk)" },
          { value: "germany", label: "🇩🇪 Витрина Germany (glassdoor.de)" },
          { value: "netherlands", label: "🇳🇱 Витрина Netherlands (glassdoor.nl)" },
          { value: "france", label: "🇫🇷 Витрина France (glassdoor.fr)" },
          { value: "spain", label: "🇪🇸 Витрина Spain (glassdoor.es)" },
          { value: "ireland", label: "🇮🇪 Витрина Ireland (glassdoor.ie)" },
          { value: "switzerland", label: "🇨🇭 Витрина Switzerland (glassdoor.ch)" },
          { value: "austria", label: "🇦🇹 Витрина Austria (glassdoor.at)" },
          { value: "belgium", label: "🇧🇪 Витрина Belgium (glassdoor.be)" },
          { value: "italy", label: "🇮🇹 Витрина Italy (glassdoor.it)" },
          { value: "usa", label: "🇺🇸 Витрина USA (glassdoor.com)" },
          { value: "canada", label: "🇨🇦 Витрина Canada (glassdoor.ca)" }
        ]
      },
      hirify: {
        label: "Локация / Рынок (Hirify)",
        remoteMechanism: "🌐 REST API • фильтр work_format=remote + worldwide_remote=true",
        hint: "Hirify: IT-агрегатор для агентов, проверяет доступность удалёнки из вашей страны",
        supportsEasyApply: false,
        options: [
          { value: "Worldwide", label: "🌐 Worldwide (Весь мир)" },
          { value: "Georgia", label: "🇬🇪 Georgia (country)" },
          { value: "Europe", label: "🇪🇺 Europe" },
          { value: "United Kingdom", label: "🇬🇧 United Kingdom" },
          { value: "Germany", label: "🇩🇪 Germany" },
          { value: "Poland", label: "🇵🇱 Poland" }
        ]
      },
      upwork: {
        label: "Охват / Рынок заказчика (Upwork • Apify)",
        remoteMechanism: "🟢 Apify Actor API • Глобальный рынок фриланс-контрактов (Worldwide Remote)",
        hint: "Upwork через Apify: собирает B2B/фриланс-заказы со ставкой, бюджетом, историей трат и страной клиента (требуется APIFY_API_KEY в .env)",
        supportsEasyApply: false,
        options: [
          { value: "Worldwide", label: "🌐 Worldwide (Весь мир — глобальный пул Upwork)" },
          { value: "EMEA", label: "🌍 EMEA (Заказчики и контракты в Европе / MENA)" },
          { value: "Europe", label: "🇪🇺 Europe (Европейские заказчики)" },
          { value: "United States", label: "🇺🇸 United States (Заказчики из США на Worldwide)" },
          { value: "United Kingdom", label: "🇬🇧 United Kingdom (Заказчики из UK)" }
        ]
      }
    };

    const SITE_REMOTE_BADGE_LABELS = {
      linkedin: "🏠 Remote / WFH",
      indeed: "🏠 Remote (DSQF7 • No Hybrid)",
      glassdoor: "🏠 Work From Home",
      hirify: "🌐 Agent API • Remote",
      upwork: "🟢 Upwork • Worldwide Contract"
    };

    function getSelectedProvider() {
      const checked = document.querySelector('input[name="siteProvider"]:checked');
      return checked ? checked.value : 'linkedin';
    }

    let hirifyFeedsCache = null;

    async function loadHirifyFeeds(force = false) {
      const select = document.getElementById('hirifyFeedSelect');
      const statusEl = document.getElementById('hirifyFeedsStatus');
      if (!select) return;

      if (hirifyFeedsCache && !force) {
        renderHirifyFeedsSelect(hirifyFeedsCache);
        return;
      }

      if (statusEl) statusEl.textContent = 'Загрузка...';
      try {
        const res = await fetch('/api/hirify/feeds');
        const data = await res.json();
        if (!data.configured) {
          if (statusEl) statusEl.textContent = 'HIRIFY_API_KEY не задан';
          select.innerHTML = '<option value="">⚠️ HIRIFY_API_KEY не установлен в .env</option>';
          return;
        }
        if (data.error) {
          if (statusEl) statusEl.textContent = 'Ошибка загрузки';
          select.innerHTML = `<option value="">⚠️ Ошибка: ${escapeHtml(data.error)}</option>`;
          return;
        }
        hirifyFeedsCache = data.feeds || [];
        renderHirifyFeedsSelect(hirifyFeedsCache);
      } catch (err) {
        if (statusEl) statusEl.textContent = 'Сбой сети';
        select.innerHTML = `<option value="">⚠️ Не удалось загрузить фильтры</option>`;
      }
    }

    function renderHirifyFeedsSelect(feeds) {
      const select = document.getElementById('hirifyFeedSelect');
      const statusEl = document.getElementById('hirifyFeedsStatus');
      if (!select) return;

      const activeFeeds = feeds.filter(f => f.is_active);
      const inactiveFeeds = feeds.filter(f => !f.is_active);

      if (statusEl) {
        statusEl.textContent = `Активных: ${activeFeeds.length} из ${feeds.length}`;
      }

      let html = `<option value="all_active">★ Все активные фильтры (${activeFeeds.map(f => f.name).join(' + ') || 'нет активных'})</option>`;

      if (activeFeeds.length > 0) {
        html += `<optgroup label="🟢 Активные фильтры">`;
        activeFeeds.forEach(f => {
          html += `<option value="${f.id}">🟢 ${escapeHtml(f.name)} (ID: ${f.id})</option>`;
        });
        html += `</optgroup>`;
      }

      if (inactiveFeeds.length > 0) {
        html += `<optgroup label="⚪ Неактивные фильтры в Hirify">`;
        inactiveFeeds.forEach(f => {
          html += `<option value="${f.id}">⚪ ${escapeHtml(f.name)} (ID: ${f.id}, неактивен)</option>`;
        });
        html += `</optgroup>`;
      }

      select.innerHTML = html;
    }

    function onHirifyModeChange() {
      const modeRadio = document.querySelector('input[name="hirifyModeRadio"]:checked');
      const mode = modeRadio ? modeRadio.value : 'feeds';
      const feedsWrap = document.getElementById('hirifyFeedsWrap');
      const searchTermsWrap = document.getElementById('searchTermsWrap');
      const locationWrap = document.getElementById('locationWrap');

      if (mode === 'feeds') {
        if (feedsWrap) feedsWrap.classList.remove('hidden');
        if (searchTermsWrap) searchTermsWrap.classList.add('hidden');
        if (locationWrap) locationWrap.classList.add('hidden');
      } else {
        if (feedsWrap) feedsWrap.classList.add('hidden');
        if (searchTermsWrap) searchTermsWrap.classList.remove('hidden');
        if (locationWrap) locationWrap.classList.remove('hidden');
      }
    }

    function onProviderChange() {
      const provider = getSelectedProvider();
      const cfg = PROVIDER_CONFIG[provider] || PROVIDER_CONFIG.linkedin;
      const locSelect = document.getElementById('location');
      const locLabel = document.getElementById('locationLabel');
      const hintEl = document.getElementById('providerHint');
      const remoteBadgeEl = document.getElementById('remoteMechanismBadge');
      const easyWrap = document.getElementById('easyApplyWrap');
      const easyInput = document.getElementById('easyApply');
      const modeBar = document.getElementById('hirifyModeBar');
      const feedsWrap = document.getElementById('hirifyFeedsWrap');
      const searchTermsWrap = document.getElementById('searchTermsWrap');
      const locationWrap = document.getElementById('locationWrap');

      locLabel.textContent = cfg.label;
      hintEl.textContent = cfg.hint;
      if (remoteBadgeEl) {
        remoteBadgeEl.textContent = cfg.remoteMechanism || '';
      }
      locSelect.innerHTML = cfg.options
        .map(o => `<option value="${escapeHtml(o.value)}">${escapeHtml(o.label)}</option>`)
        .join('');

      if (cfg.supportsEasyApply) {
        easyWrap.classList.remove('opacity-40', 'pointer-events-none');
      } else {
        easyInput.checked = false;
        easyWrap.classList.add('opacity-40', 'pointer-events-none');
      }

      if (provider === 'hirify') {
        if (modeBar) modeBar.classList.remove('hidden');
        loadHirifyFeeds();
        onHirifyModeChange();
      } else {
        if (modeBar) modeBar.classList.add('hidden');
        if (feedsWrap) feedsWrap.classList.add('hidden');
        if (searchTermsWrap) searchTermsWrap.classList.remove('hidden');
        if (locationWrap) locationWrap.classList.remove('hidden');
      }

      if (typeof cachedProviderChecks !== 'undefined' && cachedProviderChecks && cachedProviderChecks[provider]) {
        const pInfo = cachedProviderChecks[provider];
        const hoursEl = document.getElementById('hoursOld');
        if (hoursEl && pInfo.recommended_hours_old) {
          hoursEl.value = pInfo.recommended_hours_old;
        }
      }
    }

    let toastTimer = null;
    function showToast(text, durationMs = 3200) {
      const t = document.getElementById('toast');
      if (!t) return;
      t.textContent = text;
      t.classList.remove('hidden');
      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(() => t.classList.add('hidden'), durationMs);
    }

    function updateTabsText() {
      const tabs = [
        { tab: 'top', countId: 'cntTop', key: 'tab_top_text', icon: '🟢 ' },
        { tab: 'good', countId: 'cntGood', key: 'tab_good_text', icon: '🟡 ' },
        { tab: 'fair', countId: 'cntFair', key: 'tab_fair_text', icon: '🟠 ' },
        { tab: 'pending', countId: 'cntPending', key: 'tab_pending_text', icon: '⏳ ' },
        { tab: 'applied', countId: 'cntApplied', key: 'tab_applied_text', icon: '✅ ' },
        { tab: 'rejected', countId: 'cntRejected', key: 'tab_rejected_text', icon: '🗑️ ' },
        { tab: 'blacklist', countId: 'cntBadBoards', key: 'tab_blacklist_text', icon: '⛔ ' },
        { tab: 'skills', countId: 'cntSkills', key: 'tab_skills_text', icon: '🎯 ' },
      ];
      tabs.forEach(tInfo => {
        const btn = document.querySelector(`.tab-btn[data-tab="${tInfo.tab}"]`);
        if (btn) {
          const cntEl = document.getElementById(tInfo.countId);
          const cnt = cntEl ? cntEl.textContent : '0';
          btn.innerHTML = `${tInfo.icon}${t(tInfo.key)} (<span id="${tInfo.countId}">${cnt}</span>)`;
        }
      });
      const candBtn = document.querySelector('.tab-btn[data-tab="candidate"]');
      if (candBtn) {
        candBtn.textContent = t('tab_candidate');
      }
    }

    function copySnippet(key) {
      navigator.clipboard.writeText(SNIPPETS[key]);
      showToast(currentLang === 'ru' ? 'Скопировано в буфер обмена!' : 'Copied to clipboard!');
    }

    function switchTab(tab) {
      currentTab = tab;
      document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.tab === tab) {
          btn.className = 'tab-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white';
        } else if (btn.dataset.tab === 'blacklist') {
          btn.className = 'tab-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-red-950/60 text-red-300 hover:bg-red-900/60 border border-red-800/60';
        } else if (btn.dataset.tab === 'skills') {
          btn.className = 'tab-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-950/60 text-indigo-300 hover:bg-indigo-900/60 border border-indigo-800/60';
        } else {
          btn.className = 'tab-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700';
        }
      });

      const candSec = document.getElementById('candidateSection');
      const blackSec = document.getElementById('blacklistSection');
      const skillsSec = document.getElementById('skillsSection');
      const jobsSec = document.getElementById('jobsList');
      const rejBar = document.getElementById('rejectedFilterBar');
      const appBar = document.getElementById('appliedTrackerBar');
      if (rejBar) {
        if (tab === 'rejected') {
          rejBar.classList.remove('hidden');
        } else {
          rejBar.classList.add('hidden');
          rejectedSubtab = 'all';
          rejectedReasonFilter = null;
          rejectedCategoryFilter = null;
        }
      }
      if (appBar) {
        if (tab === 'applied') {
          appBar.classList.remove('hidden');
        } else {
          appBar.classList.add('hidden');
          appliedStageFilter = 'all';
          appliedCompanyReasonFilter = null;
        }
      }
      if (tab === 'candidate') {
        candSec.classList.remove('hidden');
        blackSec.classList.add('hidden');
        skillsSec.classList.add('hidden');
        jobsSec.classList.add('hidden');
        loadCandidateProfile();
      } else if (tab === 'blacklist') {
        candSec.classList.add('hidden');
        blackSec.classList.remove('hidden');
        skillsSec.classList.add('hidden');
        jobsSec.classList.add('hidden');
        loadBlacklistPanel();
      } else if (tab === 'skills') {
        candSec.classList.add('hidden');
        blackSec.classList.add('hidden');
        skillsSec.classList.remove('hidden');
        jobsSec.classList.add('hidden');
        loadSkillsMatrix();
      } else {
        candSec.classList.add('hidden');
        blackSec.classList.add('hidden');
        skillsSec.classList.add('hidden');
        jobsSec.classList.remove('hidden');
        loadJobs();
      }
    }

    let modalTargetJob = { job_id: null, company: null, title: null };
    let cachedLastOpenedJob = null;

    async function trackJobOpen(jobId) {
      try {
        const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/opened`, { method: 'POST' });
        const data = await res.json();
        if (data.last_opened_job) {
          cachedLastOpenedJob = data.last_opened_job;
          updateLastOpenedBanner(cachedLastOpenedJob);
        }
      } catch (e) {
        // ignore
      }
    }

    function updateLastOpenedBanner(info) {
      const txtEl = document.getElementById('lastOpenedText');
      const btnEl = document.getElementById('btnBanLastOpened');
      if (!txtEl || !btnEl) return;
      if (info && info.job_id) {
        txtEl.innerHTML = `<strong class="text-white">${escapeHtml(info.title || info.job_id)}</strong> @ <span class="text-indigo-300">${escapeHtml(info.company || 'Unknown')}</span> <span class="text-slate-500">(${escapeHtml(info.opened_at || '')})</span>`;
        btnEl.classList.remove('hidden');
      } else {
        txtEl.textContent = 'Пока не открывалась в этой сессии';
        btnEl.classList.add('hidden');
      }
    }

    async function pasteClipboardToInput(inputId) {
      try {
        const text = await navigator.clipboard.readText();
        if (text) {
          document.getElementById(inputId).value = text.trim();
          showToast('Вставлено из буфера обмена 📋');
        }
      } catch (err) {
        showToast('Не удалось прочитать буфер обмена — нажми Cmd+V');
      }
    }

    function extractDomainFromUrl(url) {
      if (!url) return '';
      try {
        const raw = url.includes('://') ? url : 'https://' + url;
        const host = new URL(raw).hostname.toLowerCase().replace(/^www\./, '');
        if (!host || host === 'localhost' || host === '127.0.0.1') return '';

        // Защищенные поисковые агрегаторы и капчи (никогда не считаются ATS)
        const IGNORED_DOMAINS = [
          'linkedin.com', 'hirify.me', 'indeed.com', 'glassdoor.com', 'upwork.com',
          'hcaptcha.com', 'recaptcha.net', 'google.com', 'gstatic.com', 'cloudflare.com',
          'challenges.cloudflare.com', 'arkoselabs.com', 'geetest.com', 'doubleclick.net', 'googletagmanager.com'
        ];
        if (IGNORED_DOMAINS.some(d => host === d || host.endsWith('.' + d))) {
          return '';
        }
        if (/(^|\.)(linkedin|hirify|indeed|glassdoor|upwork)\.[a-z.]+$/.test(host)) {
          return '';
        }

        const ATS_LIST = [
          'icims.com', 'cims.com', 'myworkdayjobs.com', 'workday.com',
          'taleo.net', 'successfactors.com', 'successfactors.eu',
          'greenhouse.io', 'lever.co', 'ashbyhq.com', 'smartrecruiters.com',
          'workable.com', 'breezy.hr', 'bamboohr.com', 'jobvite.com',
          'ultipro.com', 'dayforcehcm.com', 'brassring.com', 'oraclecloud.com',
          'pageuppeople.com', 'avature.net', 'recruitee.com', 'teamtailor.com',
          'personio.de', 'personio.com'
        ];
        for (const ats of ATS_LIST) {
          if (host === ats || host.endsWith('.' + ats)) return ats;
        }
        const parts = host.split('.');
        if (parts.length >= 3 && ['co', 'com', 'org', 'net', 'gov'].includes(parts[parts.length - 2]) && parts[parts.length - 1].length === 2) {
          return parts.slice(-3).join('.');
        }
        if (parts.length >= 2) {
          return parts.slice(-2).join('.');
        }
        return host;
      } catch (_) {
        return '';
      }
    }

    function openBadBoardModal(jobId, company, title, existingDomain = '') {
      modalTargetJob = { job_id: jobId, company: company, title: title };
      document.getElementById('modalJobSubtitle').textContent =
        `${title || jobId} @ ${company || 'Unknown'}`;
      document.getElementById('modalBadDomainInput').value = existingDomain || '';
      const modal = document.getElementById('badBoardModal');
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function openBadBoardModalForLastOpened() {
      if (!cachedLastOpenedJob || !cachedLastOpenedJob.job_id) return;
      const dom = cachedLastOpenedJob.ats_domain || extractDomainFromUrl(cachedLastOpenedJob.apply_url) || extractDomainFromUrl(cachedLastOpenedJob.url) || '';
      openBadBoardModal(
        cachedLastOpenedJob.job_id,
        cachedLastOpenedJob.company,
        cachedLastOpenedJob.title,
        dom
      );
    }

    function closeBadBoardModal() {
      const modal = document.getElementById('badBoardModal');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }

    function selectPresetBadDomain(domain) {
      document.getElementById('modalBadDomainInput').value = domain;
    }

    async function confirmBadBoardModal() {
      const domain_or_url = document.getElementById('modalBadDomainInput').value.trim();
      const rawDom = (domain_or_url || '').toLowerCase();
      if (domain_or_url && (/(^|\.)(linkedin|hirify|indeed|glassdoor|upwork)\.[a-z.]+$/.test(rawDom) || /hcaptcha\.com|recaptcha\.net/.test(rawDom))) {
        showToast('Поисковые агрегаторы (LinkedIn, Hirify, Upwork, Indeed, Glassdoor) нельзя блокировать. Заблокируйте только компанию!');
        return;
      }
      const reason = document.getElementById('modalBadReasonInput').value.trim() || 'Невозможно заполнить форму (в чёрном списке)';
      await fetch('/api/blacklist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain_or_url: domain_or_url || null,
          company: modalTargetJob.company || null,
          job_id: modalTargetJob.job_id || null,
          reason: reason,
          hide_job: true
        })
      });
      closeBadBoardModal();
      showToast('Борд и компания добавлены в чёрный список ⛔');
      if (currentTab === 'blacklist') {
        loadBlacklistPanel();
      } else {
        loadJobs();
      }
    }

    let currentRejectJobId = null;

    function openRejectJobModal(jobId, company, title, existingReason = '') {
      currentRejectJobId = jobId;
      const subtitleEl = document.getElementById('modalRejectJobSubtitle');
      if (subtitleEl) subtitleEl.textContent = `${title || ''} @ ${company || ''}`;
      const inputEl = document.getElementById('modalRejectReasonInput');
      if (inputEl) inputEl.value = existingReason || '';
      const modal = document.getElementById('rejectJobModal');
      if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
      }
      setTimeout(() => inputEl && inputEl.focus(), 50);
    }

    function closeRejectJobModal() {
      currentRejectJobId = null;
      const modal = document.getElementById('rejectJobModal');
      if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
      }
    }

    function selectRejectPreset(reason) {
      const input = document.getElementById('modalRejectReasonInput');
      if (input) {
        input.value = reason;
        input.focus();
      }
    }

    async function confirmRejectJobModal() {
      if (!currentRejectJobId) return;
      const input = document.getElementById('modalRejectReasonInput');
      const reason = (input ? input.value.trim() : '') || (currentLang === 'ru' ? 'Не подошла (причина не указана)' : 'Not suitable (no details given)');
      const jobId = currentRejectJobId;
      closeRejectJobModal();
      await setJobStatus(jobId, 'rejected', reason);
    }

    async function addBadDomainFromPanel() {
      const domain_or_url = document.getElementById('newBadDomainInput').value.trim();
      const reason = document.getElementById('newBadReasonInput').value.trim() || 'Невозможно заполнить форму (в чёрном списке)';
      if (!domain_or_url) {
        showToast('Укажи домен или URL (например, cims.com)');
        return;
      }
      const rawDom = domain_or_url.toLowerCase();
      if (/(^|\.)(linkedin|hirify|indeed|glassdoor|upwork)\.[a-z.]+$/.test(rawDom) || /hcaptcha\.com|recaptcha\.net/.test(rawDom)) {
        showToast('Поисковые агрегаторы (LinkedIn, Hirify, Upwork, Indeed, Glassdoor) нельзя заносить в чёрный список!');
        return;
      }
      await fetch('/api/blacklist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain_or_url,
          reason,
          hide_job: false
        })
      });
      document.getElementById('newBadDomainInput').value = '';
      showToast(`Домен добавлен в чёрный список ⛔`);
      loadBlacklistPanel();
    }

    async function removeBadDomain(domain) {
      await fetch(`/api/blacklist/domain/${encodeURIComponent(domain)}`, { method: 'DELETE' });
      showToast(`Удалено из чёрного списка: ${domain}`);
      loadBlacklistPanel();
    }

    async function removeCompanyAts(companyKey) {
      await fetch(`/api/blacklist/company/${encodeURIComponent(companyKey)}`, { method: 'DELETE' });
      showToast(`Привязка компании удалена`);
      loadBlacklistPanel();
    }

    async function loadBlacklistPanel() {
      const res = await fetch('/api/blacklist');
      const data = await res.json();
      const boards = data.boards || [];
      const companies = data.companies || [];
      document.getElementById('cntBadBoards').textContent = boards.length;

      if (data.last_opened_job) {
        cachedLastOpenedJob = data.last_opened_job;
        updateLastOpenedBanner(cachedLastOpenedJob);
      }

      const bList = document.getElementById('badDomainsList');
      if (boards.length === 0) {
        bList.innerHTML = `<div class="text-xs text-slate-500 italic p-3 bg-slate-900/40 rounded-lg">Чёрный список доменов пуст.</div>`;
      } else {
        bList.innerHTML = boards.map(b => `
          <div class="flex items-center justify-between gap-2 p-3 rounded-lg bg-slate-900 border border-red-900/40">
            <div>
              <div class="text-sm font-mono font-bold text-red-300">💩 ${escapeHtml(b.domain)}</div>
              <div class="text-xs text-slate-400">${escapeHtml(b.reason || '')}</div>
            </div>
            <button onclick="removeBadDomain('${escapeHtml(b.domain)}')" title="Удалить из чёрного списка"
              class="px-2.5 py-1 rounded bg-slate-800 hover:bg-red-900/60 text-slate-400 hover:text-white text-xs">
              ✕
            </button>
          </div>
        `).join('');
      }

      const cList = document.getElementById('badCompaniesList');
      if (companies.length === 0) {
        cList.innerHTML = `<div class="text-xs text-slate-500 italic p-3 bg-slate-900/40 rounded-lg">Пока ни одна компания не привязана к черному списку. Когда ты перейдёшь с LinkedIn на проблемный домен (например, <code>cims.com</code>) или нажмёшь кнопку «⛔ В черный список» на карточке, компания появится здесь.</div>`;
      } else {
        cList.innerHTML = companies.map(c => `
          <div class="flex items-center justify-between gap-2 p-3 rounded-lg bg-slate-900 border border-slate-800">
            <div>
              <div class="text-sm font-semibold text-white">🏢 ${escapeHtml(c.company_name || c.company_key)}</div>
              <div class="text-xs text-red-300 font-mono">↳ ATS: ${escapeHtml(c.ats_domain || '')}</div>
              ${c.sample_url ? `<div class="text-[11px] text-slate-500 truncate max-w-md">${escapeHtml(c.sample_url)}</div>` : ''}
            </div>
            <button onclick="removeCompanyAts('${escapeHtml(c.company_key)}')" title="Отвязать компанию"
              class="px-2.5 py-1 rounded bg-slate-800 hover:bg-red-900/60 text-slate-400 hover:text-white text-xs">
              ✕
            </button>
          </div>
        `).join('');
      }
    }

    async function loadCandidateProfile() {
      const res = await fetch('/api/candidate');
      const data = await res.json();
      document.getElementById('profileTextInput').value = data.profile_text || '';
      document.getElementById('cvTextInput').value = data.cv_text || '';
      const tsEl = document.getElementById('candidateUpdatedAt');
      tsEl.textContent = data.updated_at ? `Обновлено: ${data.updated_at.replace('T', ' ').slice(0, 19)} UTC` : '';

      if (data.geo_preferences) {
        const gp = data.geo_preferences;
        const curLocEl = document.getElementById('geoCurrentLocation');
        if (curLocEl) curLocEl.value = gp.current_location || '';

        const macroEl = document.getElementById('geoMacroRegions');
        if (macroEl) {
          const macros = Array.isArray(gp.allowed_macro_regions) ? gp.allowed_macro_regions.join(', ') : (gp.allowed_macro_regions || '');
          macroEl.value = macros;
        }

        const reloEl = document.getElementById('geoRelocationPolicy');
        if (reloEl) reloEl.value = gp.relocation_policy || 'with_sponsorship_only';

        const wwEl = document.getElementById('geoAllowWorldwide');
        if (wwEl) wwEl.checked = gp.allow_worldwide_remote !== false;

        const rejEl = document.getElementById('geoRejectSingleCountry');
        if (rejEl) rejEl.checked = gp.reject_unsupported_single_country !== false;

        const rejTravelEl = document.getElementById('geoRejectBusinessTravel');
        if (rejTravelEl) rejTravelEl.checked = gp.reject_business_travel !== false;

        const notesEl = document.getElementById('geoCustomNotes');
        if (notesEl) notesEl.value = gp.custom_notes || '';
      }
    }

    async function saveCandidateProfile() {
      const profile_text = document.getElementById('profileTextInput').value;
      const cv_text = document.getElementById('cvTextInput').value;

      const rawMacros = document.getElementById('geoMacroRegions')?.value || '';
      const allowed_macro_regions = rawMacros.split(',').map(s => s.trim()).filter(Boolean);

      const geo_preferences = {
        current_location: document.getElementById('geoCurrentLocation')?.value?.trim() || 'Georgia, Tbilisi (UTC+4)',
        allowed_macro_regions: allowed_macro_regions.length > 0 ? allowed_macro_regions : ['Georgia', 'Caucasus', 'Eastern Europe', 'CEE', 'EMEA'],
        relocation_policy: document.getElementById('geoRelocationPolicy')?.value || 'with_sponsorship_only',
        allow_worldwide_remote: document.getElementById('geoAllowWorldwide')?.checked !== false,
        reject_unsupported_single_country: document.getElementById('geoRejectSingleCountry')?.checked !== false,
        reject_business_travel: document.getElementById('geoRejectBusinessTravel')?.checked !== false,
        custom_notes: document.getElementById('geoCustomNotes')?.value?.trim() || ''
      };

      const res = await fetch('/api/candidate', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_text, cv_text, geo_preferences })
      });
      const data = await res.json();
      const tsEl = document.getElementById('candidateUpdatedAt');
      tsEl.textContent = data.updated_at ? `Обновлено: ${data.updated_at.replace('T', ' ').slice(0, 19)} UTC` : '';
      showToast('Профиль, CV и гео-преференции сохранены в базу данных jobs.db ✅');
    }

    function exportCandidateJson() {
      const rawMacros = document.getElementById('geoMacroRegions')?.value || '';
      const allowed_macro_regions = rawMacros.split(',').map(s => s.trim()).filter(Boolean);

      const payload = {
        profile: document.getElementById('profileTextInput').value,
        cv: document.getElementById('cvTextInput').value,
        geo_preferences: {
          current_location: document.getElementById('geoCurrentLocation')?.value?.trim() || '',
          allowed_macro_regions: allowed_macro_regions,
          relocation_policy: document.getElementById('geoRelocationPolicy')?.value || 'with_sponsorship_only',
          allow_worldwide_remote: document.getElementById('geoAllowWorldwide')?.checked !== false,
          reject_unsupported_single_country: document.getElementById('geoRejectSingleCountry')?.checked !== false,
          reject_business_travel: document.getElementById('geoRejectBusinessTravel')?.checked !== false,
          custom_notes: document.getElementById('geoCustomNotes')?.value?.trim() || ''
        }
      };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'candidate-profile-settings.json';
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 400);
    }

    async function importCandidateJson(event) {
      const file = event.target.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        const parsed = JSON.parse(text);
        if (parsed.profile !== undefined) {
          document.getElementById('profileTextInput').value = parsed.profile;
        } else if (parsed.profile_text !== undefined) {
          document.getElementById('profileTextInput').value = parsed.profile_text;
        }
        if (parsed.cv !== undefined) {
          document.getElementById('cvTextInput').value = parsed.cv;
        } else if (parsed.cv_text !== undefined) {
          document.getElementById('cvTextInput').value = parsed.cv_text;
        }
        await saveCandidateProfile();
      } catch (err) {
        alert('Ошибка чтения JSON: ' + err.message);
      }
      event.target.value = '';
    }

    async function setJobStatus(jobId, status, rejectReason = null) {
      const payload = { user_status: status };
      if (rejectReason !== null) {
        payload.user_reject_reason = rejectReason;
      }
      await fetch(`/api/jobs/${encodeURIComponent(jobId)}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (status === 'applied') {
        showToast(t('toast_applied'));
      } else if (status === 'rejected') {
        showToast(t('toast_rejected'));
      } else {
        showToast(t('toast_status_updated'));
      }
      loadJobs();
    }

    async function rescoreAll() {
      const res = await fetch('/api/jobs/rescore', { method: 'POST' });
      const data = await res.json();
      showToast(`Пересчитан скоринг для ${data.rescored} вакансий`);
      loadJobs();
    }

    async function startPipeline(enrichOnly) {
      const termsRaw = document.getElementById('searchTerms').value;
      const searchTerms = termsRaw.split(',').map(s => s.trim()).filter(Boolean);
      const provider = getSelectedProvider();
      const location = document.getElementById('location').value.trim() || 'EMEA';
      const hoursOld = parseInt(document.getElementById('hoursOld').value || '4', 10);
      const llmLimit = parseInt(document.getElementById('llmLimit').value || '50', 10);
      const easyApply = document.getElementById('easyApply').checked;
      const countryIndeed = (provider === 'indeed' || provider === 'glassdoor') ? location : 'uk';
      const siteNames = [provider];

      let hirifyMode = 'feeds';
      let hirifyFeedId = 'all_active';
      if (provider === 'hirify') {
        const modeRadio = document.querySelector('input[name="hirifyModeRadio"]:checked');
        hirifyMode = modeRadio ? modeRadio.value : 'feeds';
        const feedSelect = document.getElementById('hirifyFeedSelect');
        hirifyFeedId = feedSelect ? feedSelect.value : 'all_active';
      }

      const logContainer = document.getElementById('logContainer');
      if (logContainer) logContainer.classList.remove('hidden');
      const logOutput = document.getElementById('logOutput');
      if (logOutput) logOutput.textContent = '';
      logCursor = 0;
      updateLogButtonState(true);

      await fetch('/api/pipeline/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          search_terms: searchTerms,
          site_names: siteNames,
          location: location,
          country_indeed: countryIndeed,
          results_wanted: 50,
          hours_old: hoursOld,
          easy_apply: easyApply,
          llm_limit: llmLimit,
          enrich_only: enrichOnly,
          hirify_mode: hirifyMode,
          hirify_feed_id: hirifyFeedId
        })
      });

      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(pollPipelineStatus, 1500);
      pollPipelineStatus();
    }

    function toggleLog() {
      const container = document.getElementById('logContainer');
      if (!container) return;
      const isHidden = container.classList.contains('hidden');
      if (isHidden) {
        container.classList.remove('hidden');
      } else {
        container.classList.add('hidden');
      }
      updateLogButtonState();
    }

    function clearLog() {
      const pre = document.getElementById('logOutput');
      if (pre) pre.textContent = '';
      logCursor = 0;
      updateLogButtonState();
    }

    function updateLogButtonState(running = null) {
      const container = document.getElementById('logContainer');
      const isHidden = container ? container.classList.contains('hidden') : true;
      const btnText = document.getElementById('btnToggleLogText');
      const dot = document.getElementById('logStatusDot');
      const collapseText = document.getElementById('btnCollapseLogText');

      if (running === null) {
        running = pollTimer !== null;
      }

      if (dot) {
        if (running) {
          dot.className = 'w-2 h-2 rounded-full bg-indigo-400 animate-ping';
        } else {
          const pre = document.getElementById('logOutput');
          const hasLogs = pre && pre.textContent.trim().length > 0;
          dot.className = hasLogs ? 'w-2 h-2 rounded-full bg-emerald-400' : 'w-2 h-2 rounded-full bg-slate-500';
        }
      }

      if (btnText) {
        if (isHidden) {
          btnText.textContent = running
            ? (currentLang === 'ru' ? '⚡ Лог (выполняется...)' : '⚡ Log (running...)')
            : t('show_log');
        } else {
          btnText.textContent = t('hide_log');
        }
      }

      if (collapseText) {
        collapseText.textContent = t('hide_log');
      }
    }

    async function pollPipelineStatus() {
      try {
        const res = await fetch(`/api/pipeline/status?since=${logCursor}`);
        const data = await res.json();
        if (data.provider_checks && typeof renderProviderCheckBadges === 'function') {
          cachedProviderChecks = data.provider_checks;
          renderProviderCheckBadges();
        }
        const stopBtn = document.getElementById('btnStopPipeline');
        if (stopBtn) {
          if (data.running) {
            stopBtn.classList.remove('hidden');
          } else {
            stopBtn.classList.add('hidden');
          }
        }
        const pre = document.getElementById('logOutput');
        if (data.logs && data.logs.length > 0) {
          pre.textContent += data.logs.join('\n') + '\n';
          pre.scrollTop = pre.scrollHeight;
          logCursor = data.next_index;
          loadJobs();
        }
        const badge = document.getElementById('pipelineBadge');
        if (!data.running) {
          if (badge) {
            badge.innerHTML = `✅ ${t('pipeline_finished') || 'Пайплайн завершен'}`;
            badge.className = 'text-xs font-medium text-emerald-400';
          }
          if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
            loadJobs();
          }
          updateLogButtonState(false);
        } else {
          if (badge) {
            badge.innerHTML = `<span class="animate-ping inline-block w-2 h-2 rounded-full bg-indigo-400"></span> ${t('pipeline_running') || 'Выполняется пайплайн...'}`;
            badge.className = 'text-xs font-medium text-indigo-400 flex items-center gap-1.5';
          }
          if (!pollTimer) {
            pollTimer = setInterval(pollPipelineStatus, 1500);
          }
          updateLogButtonState(true);
        }
      } catch (err) {
        console.error('Ошибка проверки статуса пайплайна:', err);
      }
    }

    async function stopPipeline() {
      try {
        await fetch('/api/pipeline/stop', { method: 'POST' });
        showToast(currentLang === 'ru' ? '⏹️ Остановка пайплайна запрошена...' : '⏹️ Stopping pipeline...');
        pollPipelineStatus();
      } catch (err) {
        showToast('Ошибка остановки: ' + err.message);
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function escapeJsArg(str) {
      if (!str) return '';
      return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/\n/g, ' ');
    }

    async function loadJobDescriptionOnToggle(detailsEl, jobId) {
      if (!detailsEl || !detailsEl.open || detailsEl.dataset.loaded === '1') return;
      const preEl = detailsEl.querySelector('pre');
      if (!preEl) return;
      try {
        const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/description`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        preEl.textContent = data.description || '';
        detailsEl.dataset.loaded = '1';
      } catch (err) {
        preEl.textContent = 'Не удалось загрузить описание: ' + err.message;
      }
    }

    function renderJobCard(job) {
      const e = job.enrichment || {};
      const sd = job.score_details || {};
      const score = job.score;
      const isTop = score !== null && score >= 70;
      const isGood = score !== null && score >= 60 && score < 70;
      const isFair = score !== null && score >= 50 && score < 60;

      const scoreBadgeClass = isTop ? 'badge-top' : isGood ? 'badge-good' : isFair ? 'badge-fair' : 'badge-low';
      const scoreLabel = score !== null ? `🎯 Score: ${score}/100` : '⏳ Без ИИ-оценки';

      const matched = (sd.matched_skills || (e.resume_fit && e.resume_fit.matched_required) || []);
      const missing = (sd.missing_skills || (e.resume_fit && e.resume_fit.missing_required) || []);
      const breakdown = (sd.breakdown || []).join(', ');
      const responsibilities = (e.responsibilities || []).slice(0, 5);
      const requirements = (e.requirements || []).slice(0, 5);
      const locRestrictions = (e.location_restrictions || []).join(', ');
      const remoteDetail = e.remote_policy_detail || '';
      const fitSummary = (e.resume_fit && e.resume_fit.summary) ? e.resume_fit.summary : '';

      const siteKey = (job.site || 'linkedin').toLowerCase();
      const titleAndLoc = `${job.title || ''} ${job.location || ''}`.toLowerCase();
      const detectedRemoteByKeyword = /remote|work from home|\bwfh\b|télétravail|anywhere|distributed/.test(titleAndLoc);
      const isRemoteFlag = job.is_remote === 1 || job.is_remote === true || detectedRemoteByKeyword;
      const remoteBadgeText = isRemoteFlag
        ? (SITE_REMOTE_BADGE_LABELS[siteKey] || '🏠 Remote')
        : (remoteDetail ? `🏠 ${remoteDetail}` : '');

      const isBadBoard = Boolean(job.is_bad_board);
      const atsDomain = job.ats_domain || extractDomainFromUrl(job.apply_url) || extractDomainFromUrl(job.url) || '';
      const cardBorderClass = isBadBoard
        ? 'border-red-600/80 bg-red-950/15 hover:border-red-500'
        : 'hover:border-slate-600';

      return `
        <article class="card rounded-xl p-5 shadow transition ${cardBorderClass}">
          ${isBadBoard ? `
            <div class="mb-3 px-3.5 py-2.5 rounded-lg bg-red-950/90 border border-red-600 text-red-200 text-xs font-semibold flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <span class="text-base">⛔</span>
                <span>ВНИМАНИЕ: В ЧЁРНОМ СПИСКЕ <code class="px-1.5 py-0.5 rounded bg-red-900/90 text-white font-mono">${escapeHtml(atsDomain || 'в чёрном списке')}</code> — ${escapeHtml(job.bad_board_reason || 'форму невозможно заполнить')}! Не трать время.</span>
              </div>
              ${job.user_status !== 'hidden' ? `
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'hidden')" class="px-2.5 py-1 rounded bg-red-800 hover:bg-red-700 text-white text-xs">
                  🗑️ Скрыть сразу
                </button>
              ` : ''}
            </div>
          ` : ''}

          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="space-y-1">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-xs font-bold px-2.5 py-1 rounded-md ${scoreBadgeClass}">
                  ${isTop ? '🟢 TOP MATCH • ' : isGood ? '🟡 GOOD MATCH • ' : ''}${scoreLabel}
                </span>
                <span class="text-xs px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 uppercase font-semibold">${escapeHtml(job.site || 'linkedin')}</span>
                ${atsDomain ? `<span class="text-xs px-2 py-0.5 rounded ${isBadBoard ? 'bg-red-950 text-red-300 border border-red-700 font-bold' : 'bg-slate-800 text-slate-300 border border-slate-700'} font-mono">${isBadBoard ? '💩 ' : '🌐 ATS: '}${escapeHtml(atsDomain)}</span>` : ''}
                ${remoteBadgeText ? `<span class="text-xs px-2 py-0.5 rounded bg-teal-950/80 text-teal-300 border border-teal-800/60 font-medium">${escapeHtml(remoteBadgeText)}</span>` : ''}
                ${job.location && job.location !== 'None' ? `<span class="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">📍 ${escapeHtml(job.location)}</span>` : ''}
                ${job.tier ? `<span class="text-xs px-2.5 py-1 rounded-md bg-slate-800 text-slate-200 border border-slate-700">${escapeHtml(job.tier)}</span>` : ''}
                ${job.seniority_level ? `<span class="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">${escapeHtml(job.seniority_level)}</span>` : ''}
                ${job.salary ? `<span class="text-xs px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">💰 ${escapeHtml(job.salary)}</span>` : ''}
                ${job.user_status === 'saved' ? `<span class="text-xs px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 font-semibold">⭐ ${currentLang === 'ru' ? 'Восстановлено' : 'Restored'}</span>` : ''}
                ${job.rejection_reason_display && job.rejection_source === 'auto' ? `<span class="text-xs px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/70">🤖 ${escapeHtml(job.rejection_reason_display)}</span>` : (job.reject_reason ? `<span class="text-xs px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800">Причина: ${escapeHtml(job.reject_reason)}</span>` : '')}
              </div>

              <h2 class="text-lg font-bold text-white pt-1">
                <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener" onclick="trackJobOpen('${escapeJsArg(job.job_id)}')" class="hover:text-indigo-400 underline decoration-slate-600 underline-offset-4">
                  ${escapeHtml(job.title)}
                </a>
                <span class="text-slate-400 font-normal text-base"> @ ${escapeHtml(job.company || 'Unknown')}</span>
              </h2>

              <div class="text-xs text-slate-400 flex flex-wrap gap-3 items-center">
                <span>📅 ${escapeHtml(job.date_posted || '')}</span>
                <code class="text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded">${escapeHtml(job.url)}</code>
                ${job.apply_url ? `<a href="${escapeHtml(job.apply_url)}" target="_blank" rel="noopener" onclick="trackJobOpen('${escapeJsArg(job.job_id)}')" class="text-indigo-400 hover:underline font-mono">⚡ ${currentLang === 'ru' ? 'Прямой Apply URL ↗' : 'Direct Apply URL ↗'}</a>` : ''}
                ${job.industry ? `<span>🏢 ${escapeHtml(job.industry)}</span>` : ''}
              </div>
            </div>

            <!-- Action buttons -->
            <div class="flex flex-wrap items-center gap-2">
              <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener" onclick="trackJobOpen('${escapeJsArg(job.job_id)}')"
                class="px-3.5 py-1.5 rounded-lg ${isBadBoard ? 'bg-red-900/70 hover:bg-red-800 text-red-200 border border-red-700' : 'bg-indigo-600 hover:bg-indigo-500 text-white'} text-xs font-semibold transition">
                ${isBadBoard ? t('btn_open_job_bad') : t('btn_open_job')}
              </a>
              ${job.user_status !== 'applied' ? `
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'applied')"
                  class="px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition">
                  ${t('btn_applied_done')}
                </button>
              ` : `
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'new')"
                  class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition">
                  ${t('btn_return_new')}
                </button>
              `}
              ${(job.user_status === 'rejected' || job.user_status === 'hidden' || job.user_status === 'saved') ? `
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'new')"
                  class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition" title="${t('btn_return_new')}">
                  ${t('btn_return_new')}
                </button>
              ` : `
                <button onclick="openRejectJobModal('${escapeJsArg(job.job_id)}', '${escapeJsArg(job.company)}', '${escapeJsArg(job.title)}', '${escapeJsArg(job.user_reject_reason || '')}')"
                  class="px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 text-xs font-medium transition"
                  title="${t('btn_not_fit_title')}">
                  ${t('btn_not_fit')}
                </button>
              `}
              <button onclick="openBadBoardModal('${escapeJsArg(job.job_id)}', '${escapeJsArg(job.company)}', '${escapeJsArg(job.title)}', '${escapeJsArg(atsDomain)}')"
                title="Blacklist job board and company"
                class="px-2.5 py-1.5 rounded-lg bg-red-950/50 hover:bg-red-900/80 text-red-300 border border-red-800/60 text-xs font-medium transition">
                ${t('btn_blacklist_job')}
              </button>
              ${job.user_status !== 'hidden' ? `
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'hidden')"
                  class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-red-950/60 text-slate-400 hover:text-red-300 border border-slate-700 text-xs transition" title="${t('btn_hide_job')}">
                  🗑️
                </button>
              ` : ''}
            </div>
          </div>

          ${job.user_status === 'applied' ? (() => {
            const st = job.application_stage || 'applied';
            const rsn = job.company_reject_reason || '';
            const compName = (job.company || '').trim();
            const fallbackGmailUrl = (compName && compName.toLowerCase() !== 'unknown' && compName.toLowerCase() !== 'confidential')
              ? `https://mail.google.com/mail/u/0/#search/${encodeURIComponent('"' + compName + '"')}`
              : '';
            const emailUrl = job.application_email_url || (st === 'interview' ? fallbackGmailUrl : '');
            let boxClass = 'bg-slate-900/80 border-slate-700/80 text-slate-300';
            let badgeHtml = `<span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-semibold">⏳ ${currentLang === 'ru' ? 'Отправлено • Ждём ответа' : 'Sent • Waiting for reply'}</span>`;
            if (st === 'confirmed') {
              boxClass = 'bg-sky-950/40 border-sky-700/60 text-sky-200';
              badgeHtml = `<span class="px-2.5 py-0.5 rounded bg-sky-900/80 text-sky-200 border border-sky-600 font-semibold">📩 ${currentLang === 'ru' ? 'Подтверждение получено' : 'Confirmation received'}</span>`;
            } else if (st === 'interview') {
              boxClass = 'bg-emerald-950/50 border-emerald-600/80 text-emerald-200';
              badgeHtml = `<span class="px-2.5 py-0.5 rounded bg-emerald-800/90 text-white border border-emerald-500 font-bold shadow">🎤 ${currentLang === 'ru' ? 'HR-скрининг / Интервью!' : 'HR Screening / Interview!'}</span>`;
            } else if (st === 'rejected_by_company') {
              boxClass = 'bg-rose-950/45 border-rose-700/70 text-rose-200';
              badgeHtml = `<span class="px-2.5 py-0.5 rounded bg-rose-900/80 text-rose-200 border border-rose-600 font-semibold">❌ ${currentLang === 'ru' ? 'Отказ от компании' : 'Rejected by company'}</span>`;
            }
            return `
              <div class="mt-3 text-xs ${boxClass} border rounded-lg px-3.5 py-2.5 flex flex-wrap items-center justify-between gap-2">
                <div class="flex flex-wrap items-center gap-2">
                  ${badgeHtml}
                  ${rsn ? `<span class="text-xs font-medium">${st === 'rejected_by_company' ? `<strong>${currentLang === 'ru' ? 'Причина:' : 'Reason:'}</strong> ` : ''}${escapeHtml(rsn)}</span>` : ''}
                  ${emailUrl ? `
                    <a href="${escapeHtml(emailUrl)}" target="_blank" rel="noopener" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-emerald-700 hover:bg-emerald-600 text-white font-semibold shadow transition">
                      ✉️ ${currentLang === 'ru' ? 'Открыть письмо ↗' : 'Open Email ↗'}
                    </a>
                  ` : ''}
                </div>
                <div class="flex flex-wrap items-center gap-1.5">
                  <button onclick="quickSetCompanyStage('${escapeJsArg(job.job_id)}', 'confirmed')" class="px-2 py-1 rounded ${st === 'confirmed' ? 'bg-sky-700 text-white font-semibold' : 'bg-slate-800 hover:bg-slate-700 text-sky-300'} border border-sky-800/60 text-[11px] transition" title="${currentLang === 'ru' ? 'Отметить получение подтверждения' : 'Mark confirmation received'}">
                    📩 ${currentLang === 'ru' ? 'Подтверждено' : 'Confirmed'}
                  </button>
                  <button onclick="openCompanyStageModal('${escapeJsArg(job.job_id)}', '${escapeJsArg(job.company)}', '${escapeJsArg(job.title)}', 'interview', '${escapeJsArg(rsn)}', '${escapeJsArg(job.application_email_url || '')}')" class="px-2 py-1 rounded ${st === 'interview' ? 'bg-emerald-700 text-white font-semibold' : 'bg-slate-800 hover:bg-slate-700 text-emerald-300'} border border-emerald-800/60 text-[11px] transition" title="${currentLang === 'ru' ? 'Отметить приглашение на HR-скрининг или интервью' : 'Mark HR screening / interview invite'}">
                    🎤 ${currentLang === 'ru' ? 'Интервью' : 'Interview'}
                  </button>
                  <button onclick="openCompanyStageModal('${escapeJsArg(job.job_id)}', '${escapeJsArg(job.company)}', '${escapeJsArg(job.title)}', 'rejected_by_company', '${escapeJsArg(rsn)}', '${escapeJsArg(job.application_email_url || '')}')" class="px-2 py-1 rounded ${st === 'rejected_by_company' ? 'bg-rose-700 text-white font-semibold' : 'bg-slate-800 hover:bg-slate-700 text-rose-300'} border border-rose-800/60 text-[11px] transition" title="${currentLang === 'ru' ? 'Отметить отказ от компании и указать причину' : 'Mark company rejection & reason'}">
                    ❌ ${currentLang === 'ru' ? 'Отказ компании' : 'Rejected'}
                  </button>
                  <button onclick="openCompanyStageModal('${escapeJsArg(job.job_id)}', '${escapeJsArg(job.company)}', '${escapeJsArg(job.title)}', '${escapeJsArg(st)}', '${escapeJsArg(rsn)}', '${escapeJsArg(job.application_email_url || '')}')" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[11px] transition" title="${currentLang === 'ru' ? 'Изменить статус / комментарий / ссылку на письмо' : 'Edit status / note / email link'}">
                    ✏️
                  </button>
                </div>
              </div>
            `;
          })() : ''}

          ${job.rejection_source === 'user' ? `
            <div class="mt-3 text-xs text-rose-200 bg-rose-950/40 border border-rose-800/60 rounded-lg px-3 py-2 flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <span class="text-sm">${job.user_status === 'hidden' ? '🗑️' : '❌'}</span>
                <div>
                  <strong>${job.user_status === 'hidden' ? (t('user_hidden_reason') || 'Скрыто в корзину') : (t('user_reject_reason_label') + ':')}</strong>
                  ${job.user_status !== 'hidden' ? `<span>${escapeHtml(job.user_reject_reason || 'Без указания причины')}</span>` : ''}
                </div>
              </div>
              <div class="flex items-center gap-2">
                ${job.user_status !== 'hidden' ? `
                  <button onclick="openRejectJobModal('${escapeJsArg(job.job_id)}', '${escapeJsArg(job.company)}', '${escapeJsArg(job.title)}', '${escapeJsArg(job.user_reject_reason || '')}')" class="text-xs text-rose-400 hover:text-rose-200 underline whitespace-nowrap">
                    ${t('btn_edit_reason')}
                  </button>
                ` : ''}
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'new')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition">
                  ${t('btn_return_new')}
                </button>
              </div>
            </div>
          ` : (job.rejection_source === 'auto' ? `
            <div class="mt-3 text-xs text-amber-200 bg-amber-950/40 border border-amber-800/60 rounded-lg px-3 py-2 flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <span class="text-sm">🤖</span>
                <div>
                  <strong>${currentLang === 'ru' ? 'Отсеяно фильтром / ИИ:' : 'Auto-filtered by:'}</strong>
                  <span>${escapeHtml(job.rejection_reason_display || job.reject_reason || 'Не соответствует критериям')}</span>
                </div>
              </div>
              <button onclick="restoreAutoRejectedJob('${escapeJsArg(job.job_id)}')" class="px-2.5 py-1 rounded bg-emerald-900/70 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 text-xs font-medium transition" title="${currentLang === 'ru' ? 'Одобрить и вернуть в активный список (сухой остаток)' : 'Approve and restore to active list'}">
                ${t('btn_restore_to_feed')}
              </button>
            </div>
          ` : (job.user_status === 'saved' ? `
            <div class="mt-3 text-xs text-emerald-200 bg-emerald-950/40 border border-emerald-800/60 rounded-lg px-3 py-2 flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <span class="text-sm">⭐</span>
                <div>
                  <strong>${currentLang === 'ru' ? 'Восстановлено вами вручную' : 'Manually restored to active list'}</strong>
                </div>
              </div>
              <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'new')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition">
                ${t('btn_return_new')}
              </button>
            </div>
          ` : ''))}

          ${fitSummary ? `
            <div class="mt-3 text-sm text-indigo-200 bg-indigo-950/40 border border-indigo-800/50 rounded-lg px-3 py-2">
              <strong>${t('fit_summary_label')}</strong> ${escapeHtml(fitSummary)}
            </div>
          ` : ''}

          <!-- Совпавшие и недостающие навыки -->
          ${(matched.length > 0 || missing.length > 0) ? `
            <div class="mt-3 space-y-1.5 text-xs">
              ${matched.length > 0 ? `
                <div class="flex flex-wrap items-center gap-1.5">
                  <span class="text-slate-400 font-medium">✅ ${currentLang === 'ru' ? 'Совпало' : 'Matched'} (${matched.length}):</span>
                  ${matched.map(s => `<span class="px-2 py-0.5 rounded chip-match font-mono">${escapeHtml(s)}</span>`).join('')}
                </div>
              ` : ''}
              ${missing.length > 0 ? `
                <div class="flex flex-wrap items-center gap-1.5">
                  <span class="text-slate-400 font-medium">⚠️ ${currentLang === 'ru' ? 'Не указано в резюме' : 'Missing from CV'} (${missing.length}):</span>
                  ${missing.map(s => `<span class="px-2 py-0.5 rounded chip-miss font-mono">${escapeHtml(s)}</span>`).join('')}
                </div>
              ` : ''}
            </div>
          ` : ''}

          ${breakdown ? `
            <div class="mt-2 text-xs text-slate-400 italic">
              📊 ${currentLang === 'ru' ? 'Скоринг детали:' : 'Score breakdown:'} ${escapeHtml(breakdown)}
            </div>
          ` : ''}

          ${(locRestrictions || remoteDetail) ? `
            <div class="mt-2 text-xs text-slate-300 bg-slate-900/70 rounded-lg px-3 py-1.5 border border-slate-800">
              📍 <strong>Условия локации / Remote:</strong>
              ${locRestrictions ? `Ограничения: <span class="text-amber-300">${escapeHtml(locRestrictions)}</span>` : ''}
              ${remoteDetail ? ` • Формат: <span class="text-emerald-300">${escapeHtml(remoteDetail)}</span>` : ''}
            </div>
          ` : ''}

          <!-- Структурированная выжимка из JobEnrichment -->
          ${(responsibilities.length > 0 || requirements.length > 0) ? `
            <div class="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-800 text-xs text-slate-300">
              ${responsibilities.length > 0 ? `
                <div>
                  <h4 class="font-semibold text-slate-200 mb-1">🛠️ Чем предстоит заниматься:</h4>
                  <ul class="list-disc list-inside space-y-0.5 text-slate-400">
                    ${responsibilities.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
                  </ul>
                </div>
              ` : ''}
              ${requirements.length > 0 ? `
                <div>
                  <h4 class="font-semibold text-slate-200 mb-1">📋 Ключевые требования:</h4>
                  <ul class="list-disc list-inside space-y-0.5 text-slate-400">
                    ${requirements.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
                  </ul>
                </div>
              ` : ''}
            </div>
          ` : ''}

          <!-- Спойлер с полным текстом описания -->
          ${(job.description || job.has_description) ? `
            <details class="mt-3 pt-2 border-t border-slate-800/60 text-xs"
              ${job.description ? 'data-loaded="1"' : `ontoggle="loadJobDescriptionOnToggle(this, '${escapeJsArg(job.job_id)}')"`}>
              <summary class="cursor-pointer text-slate-400 hover:text-slate-200 select-none">
                📄 Показать оригинальный текст вакансии
              </summary>
              <pre class="mt-2 p-3 rounded-lg bg-slate-950 text-slate-300 whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-y-auto">${job.description ? escapeHtml(job.description) : 'Загрузка текста вакансии...'}</pre>
            </details>
          ` : ''}
        </article>
      `;
    }

    let cachedJobs = [];
    let cachedStats = {};

    let rejectedSubtab = 'all'; // 'all' | 'user' | 'auto'
    let rejectedReasonFilter = null;
    let rejectedCategoryFilter = null;

    function setRejectedSubtab(subtab) {
      rejectedSubtab = subtab;
      rejectedReasonFilter = null;
      rejectedCategoryFilter = null;
      renderJobsList();
    }

    function setRejectedReasonFilter(reason) {
      rejectedReasonFilter = (rejectedReasonFilter === reason) ? null : reason;
      renderJobsList();
    }

    function setRejectedCategoryFilter(category) {
      rejectedCategoryFilter = (rejectedCategoryFilter === category) ? null : category;
      renderJobsList();
    }

    async function restoreAutoRejectedJob(jobId) {
      await setJobStatus(jobId, 'saved');
      showToast(t('toast_job_restored'));
    }

    function renderRejectedFilterBar() {
      const bar = document.getElementById('rejectedFilterBar');
      if (!bar) return;

      const userJobs = (cachedJobs || []).filter(j => j.rejection_source === 'user');
      const autoJobs = (cachedJobs || []).filter(j => j.rejection_source === 'auto');

      const cntAll = document.getElementById('cntSubtabAll');
      const cntUser = document.getElementById('cntSubtabUser');
      const cntAuto = document.getElementById('cntSubtabAuto');
      if (cntAll) cntAll.textContent = (cachedJobs || []).length;
      if (cntUser) cntUser.textContent = userJobs.length;
      if (cntAuto) cntAuto.textContent = autoJobs.length;

      const allBtn = document.getElementById('btnSubtabAll');
      const userBtn = document.getElementById('btnSubtabUser');
      const autoBtn = document.getElementById('btnSubtabAuto');
      const activeBtnClass = 'px-3 py-1.5 rounded-lg text-xs font-semibold transition bg-indigo-600 text-white shadow';
      const inactiveBtnClass = 'px-3 py-1.5 rounded-lg text-xs font-medium transition bg-slate-800 text-slate-300 hover:bg-slate-700';
      if (allBtn) allBtn.className = (rejectedSubtab === 'all') ? activeBtnClass : inactiveBtnClass;
      if (userBtn) userBtn.className = (rejectedSubtab === 'user') ? activeBtnClass : inactiveBtnClass;
      if (autoBtn) autoBtn.className = (rejectedSubtab === 'auto') ? activeBtnClass : inactiveBtnClass;

      const userWrap = document.getElementById('rejectedUserReasonsWrap');
      const autoWrap = document.getElementById('rejectedAutoCategoriesWrap');

      if (rejectedSubtab === 'user') {
        userWrap?.classList.remove('hidden');
        autoWrap?.classList.add('hidden');
      } else if (rejectedSubtab === 'auto') {
        userWrap?.classList.add('hidden');
        autoWrap?.classList.remove('hidden');
      } else {
        userWrap?.classList.remove('hidden');
        autoWrap?.classList.remove('hidden');
      }

      // Причины, указанные пользователем
      const userChipsContainer = document.getElementById('rejectedUserReasonsChips');
      if (userChipsContainer) {
        const reasonCounts = {};
        userJobs.forEach(j => {
          const r = j.rejection_reason_display || (j.user_status === 'hidden' ? (t('user_hidden_reason') || 'Скрыто в корзину') : 'Без указания причины');
          reasonCounts[r] = (reasonCounts[r] || 0) + 1;
        });

        const activeChipClass = 'px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-600 text-white shadow cursor-pointer transition';
        const inactiveChipClass = 'px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-300 cursor-pointer transition';

        let html = `
          <button onclick="setRejectedReasonFilter(null)" class="${!rejectedReasonFilter ? activeChipClass : inactiveChipClass}">
            ${t('all_reasons_chip')} (${userJobs.length})
          </button>
        `;

        Object.entries(reasonCounts)
          .sort((a, b) => b[1] - a[1])
          .forEach(([reason, count]) => {
            const isAct = rejectedReasonFilter === reason;
            html += `
              <button onclick="setRejectedReasonFilter('${escapeJsArg(reason)}')" class="${isAct ? activeChipClass : inactiveChipClass}">
                ${escapeHtml(reason)} <span class="opacity-80 font-mono">(${count})</span>
              </button>
            `;
          });
        userChipsContainer.innerHTML = html;
      }

      // Категории автоматического отсева
      const autoChipsContainer = document.getElementById('rejectedAutoCategoriesChips');
      if (autoChipsContainer) {
        const catCounts = {};
        autoJobs.forEach(j => {
          const c = j.rejection_category || 'other';
          catCounts[c] = (catCounts[c] || 0) + 1;
        });

        const activeCatClass = 'px-2.5 py-1 rounded-md text-xs font-semibold bg-indigo-600 text-white shadow cursor-pointer transition';
        const inactiveCatClass = 'px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-300 cursor-pointer transition';

        let html = `
          <button onclick="setRejectedCategoryFilter(null)" class="${!rejectedCategoryFilter ? activeCatClass : inactiveCatClass}">
            ${t('all_categories_chip')} (${autoJobs.length})
          </button>
        `;

        Object.entries(catCounts)
          .sort((a, b) => b[1] - a[1])
          .forEach(([cat, count]) => {
            const isAct = rejectedCategoryFilter === cat;
            const catTitle = t('cat_' + cat) || cat;
            html += `
              <button onclick="setRejectedCategoryFilter('${escapeJsArg(cat)}')" class="${isAct ? activeCatClass : inactiveCatClass}">
                ${escapeHtml(catTitle)} <span class="opacity-80 font-mono">(${count})</span>
              </button>
            `;
          });
        autoChipsContainer.innerHTML = html;
      }
    }

    let appliedStageFilter = 'all'; // 'all' | 'applied' | 'confirmed' | 'interview' | 'rejected_by_company'
    let appliedCompanyReasonFilter = null;

    function setAppliedStageFilter(stage) {
      appliedStageFilter = stage;
      appliedCompanyReasonFilter = null;
      renderJobsList();
    }

    function setAppliedCompanyReasonFilter(reason) {
      appliedCompanyReasonFilter = (appliedCompanyReasonFilter === reason) ? null : reason;
      renderJobsList();
    }

    function renderAppliedTrackerBar() {
      const bar = document.getElementById('appliedTrackerBar');
      if (!bar) return;

      const allJobs = cachedJobs || [];
      const waitingJobs = allJobs.filter(j => (j.application_stage || 'applied') === 'applied');
      const confirmedJobs = allJobs.filter(j => j.application_stage === 'confirmed');
      const interviewJobs = allJobs.filter(j => j.application_stage === 'interview');
      const rejectedJobs = allJobs.filter(j => j.application_stage === 'rejected_by_company');

      const setCnt = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };
      setCnt('cntAppliedAll', allJobs.length);
      setCnt('cntAppliedWaiting', waitingJobs.length);
      setCnt('cntAppliedConfirmed', confirmedJobs.length);
      setCnt('cntAppliedInterview', interviewJobs.length);
      setCnt('cntAppliedRejected', rejectedJobs.length);

      const btnMap = {
        all: { id: 'btnAppliedStageAll', active: 'px-3 py-1.5 rounded-lg text-xs font-semibold transition bg-indigo-600 text-white shadow', inactive: 'px-3 py-1.5 rounded-lg text-xs font-medium transition bg-slate-800 text-slate-300 hover:bg-slate-700' },
        applied: { id: 'btnAppliedStageWaiting', active: 'px-3 py-1.5 rounded-lg text-xs font-semibold transition bg-slate-600 text-white shadow', inactive: 'px-3 py-1.5 rounded-lg text-xs font-medium transition bg-slate-800 text-slate-300 hover:bg-slate-700' },
        confirmed: { id: 'btnAppliedStageConfirmed', active: 'px-3 py-1.5 rounded-lg text-xs font-semibold transition bg-sky-600 text-white shadow', inactive: 'px-3 py-1.5 rounded-lg text-xs font-medium transition bg-slate-800 text-sky-300 hover:bg-slate-700' },
        interview: { id: 'btnAppliedStageInterview', active: 'px-3 py-1.5 rounded-lg text-xs font-semibold transition bg-emerald-600 text-white shadow', inactive: 'px-3 py-1.5 rounded-lg text-xs font-medium transition bg-slate-800 text-emerald-300 hover:bg-slate-700' },
        rejected_by_company: { id: 'btnAppliedStageRejected', active: 'px-3 py-1.5 rounded-lg text-xs font-semibold transition bg-rose-600 text-white shadow', inactive: 'px-3 py-1.5 rounded-lg text-xs font-medium transition bg-slate-800 text-rose-300 hover:bg-slate-700' },
      };

      Object.entries(btnMap).forEach(([stageKey, cfg]) => {
        const el = document.getElementById(cfg.id);
        if (el) el.className = (appliedStageFilter === stageKey) ? cfg.active : cfg.inactive;
      });

      const reasonsWrap = document.getElementById('appliedCompanyReasonsWrap');
      const reasonsChips = document.getElementById('appliedCompanyReasonsChips');
      if (reasonsWrap && reasonsChips) {
        if (rejectedJobs.length > 0 && (appliedStageFilter === 'all' || appliedStageFilter === 'rejected_by_company')) {
          reasonsWrap.classList.remove('hidden');
          const reasonCounts = {};
          rejectedJobs.forEach(j => {
            const r = (j.company_reject_reason || (currentLang === 'ru' ? 'Без указания причины в письме' : 'No specific reason stated')).trim();
            reasonCounts[r] = (reasonCounts[r] || 0) + 1;
          });

          const activeChip = 'px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-600 text-white shadow cursor-pointer transition';
          const inactiveChip = 'px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 border border-slate-700 hover:border-slate-500 text-rose-200 cursor-pointer transition';

          let html = `
            <button onclick="setAppliedCompanyReasonFilter(null)" class="${!appliedCompanyReasonFilter ? activeChip : inactiveChip}">
              ${t('all_reasons_chip')} (${rejectedJobs.length})
            </button>
          `;
          Object.entries(reasonCounts)
            .sort((a, b) => b[1] - a[1])
            .forEach(([reason, cnt]) => {
              const isAct = appliedCompanyReasonFilter === reason;
              html += `
                <button onclick="setAppliedCompanyReasonFilter('${escapeJsArg(reason)}')" class="${isAct ? activeChip : inactiveChip}">
                  ${escapeHtml(reason)} <span class="opacity-80 font-mono">(${cnt})</span>
                </button>
              `;
            });
          reasonsChips.innerHTML = html;
        } else {
          reasonsWrap.classList.add('hidden');
        }
      }
    }

    function renderJobsList() {
      const container = document.getElementById('jobsList');
      if (!container) return;

      if (currentTab === 'rejected') {
        renderRejectedFilterBar();
      } else if (currentTab === 'applied') {
        renderAppliedTrackerBar();
      }

      let jobsToRender = cachedJobs || [];
      if (currentTab === 'applied') {
        if (appliedStageFilter !== 'all') {
          jobsToRender = jobsToRender.filter(j => (j.application_stage || 'applied') === appliedStageFilter);
        }
        if (appliedCompanyReasonFilter) {
          jobsToRender = jobsToRender.filter(j => {
            if (j.application_stage !== 'rejected_by_company') return false;
            const r = (j.company_reject_reason || (currentLang === 'ru' ? 'Без указания причины в письме' : 'No specific reason stated')).trim();
            return r === appliedCompanyReasonFilter;
          });
        }
        const tipEl = document.getElementById('appliedActiveFilterTip');
        if (tipEl) {
          tipEl.textContent = `${currentLang === 'ru' ? 'Показано' : 'Showing'}: ${jobsToRender.length} ${currentLang === 'ru' ? 'из' : 'of'} ${(cachedJobs || []).length}`;
        }
      } else if (currentTab === 'rejected') {
        if (rejectedSubtab === 'user') {
          jobsToRender = jobsToRender.filter(j => j.rejection_source === 'user');
        } else if (rejectedSubtab === 'auto') {
          jobsToRender = jobsToRender.filter(j => j.rejection_source === 'auto');
        }

        if (rejectedReasonFilter) {
          jobsToRender = jobsToRender.filter(j => {
            const r = j.rejection_reason_display || (j.user_status === 'hidden' ? (t('user_hidden_reason') || 'Скрыто в корзину') : 'Без указания причины');
            return r === rejectedReasonFilter;
          });
        }
        if (rejectedCategoryFilter) {
          jobsToRender = jobsToRender.filter(j => (j.rejection_category || 'other') === rejectedCategoryFilter);
        }

        const tipEl = document.getElementById('rejectedActiveFilterTip');
        if (tipEl) {
          const filterDesc = rejectedReasonFilter ? ` • ${currentLang === 'ru' ? 'Причина' : 'Reason'}: «${rejectedReasonFilter}»` : (rejectedCategoryFilter ? ` • ${currentLang === 'ru' ? 'Категория' : 'Category'}: «${t('cat_' + rejectedCategoryFilter) || rejectedCategoryFilter}»` : '');
          tipEl.textContent = `${currentLang === 'ru' ? 'Показано' : 'Showing'}: ${jobsToRender.length} ${currentLang === 'ru' ? 'из' : 'of'} ${(cachedJobs || []).length}${filterDesc}`;
        }
      }

      if (!jobsToRender || jobsToRender.length === 0) {
        const pendingCount = cachedStats.pending_llm || 0;
        const noJobsText = (currentLang === 'ru') ? 'В этой выборке пока нет вакансий.' : 'No vacancies in this view yet.';
        const pendingTip = (currentLang === 'ru')
          ? `В базе есть ${pendingCount} скачанных вакансий, ожидающих ИИ-разбора — нажми кнопку <strong>«🧠 Только ИИ»</strong> выше!`
          : `There are ${pendingCount} scraped vacancies awaiting AI analysis in DB — click <strong>«🧠 AI Only»</strong> above!`;
        container.innerHTML = `
          <div class="card rounded-xl p-10 text-center text-slate-400">
            <p class="text-base">${noJobsText}</p>
            ${pendingCount > 0 ? `<p class="text-xs mt-2 text-indigo-400">${pendingTip}</p>` : ''}
          </div>
        `;
        return;
      }
      container.innerHTML = jobsToRender.map(renderJobCard).join('');
    }

    async function loadJobs() {
      try {
        const res = await fetch(`/api/jobs?tab=${encodeURIComponent(currentTab)}`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        const s = data.stats || {};
        cachedStats = s;
        cachedJobs = data.jobs || [];

        const setTxt = (id, val) => {
          const el = document.getElementById(id);
          if (el) el.textContent = val;
        };

        setTxt('cntTotal', s.total_in_db || 0);
        setTxt('cntTop', s.top_match || 0);
        setTxt('cntGood', s.good_match || 0);
        setTxt('cntFair', s.fair_match || 0);
        setTxt('cntPending', s.pending_llm || 0);
        setTxt('cntApplied', s.applied || 0);
        setTxt('cntRejected', s.rejected || 0);
        if (s.bad_boards_count !== undefined) {
          setTxt('cntBadBoards', s.bad_boards_count);
        }
        if (data.last_opened_job) {
          cachedLastOpenedJob = data.last_opened_job;
          updateLastOpenedBanner(cachedLastOpenedJob);
        }

        renderJobsList();
      } catch (err) {
        console.error('Failed to load jobs:', err);
      }
    }

    let cachedSkillsMatrix = { categories: [], skills: [] };

    async function loadSkillsMatrix() {
      try {
        const res = await fetch('/api/skills/matrix');
        if (!res.ok) throw new Error('Ошибка загрузки матрицы');
        cachedSkillsMatrix = await res.json();
        const cntEl = document.getElementById('cntSkills');
        if (cntEl) cntEl.textContent = (cachedSkillsMatrix.skills || []).length;
        renderSkillsMatrix(cachedSkillsMatrix);
      } catch (err) {
        showToast('Ошибка загрузки матрицы навыков: ' + err.message);
      }
    }

    function renderSkillsMatrix(data) {
      const container = document.getElementById('skillsCategoriesContainer');
      if (!container) return;
      const categories = data.categories || [];
      const skills = data.skills || [];

      const skillsByCat = {};
      skills.forEach(s => {
        if (!skillsByCat[s.category_id]) skillsByCat[s.category_id] = [];
        skillsByCat[s.category_id].push(s);
      });

      if (categories.length === 0) {
        container.innerHTML = `
          <div class="card rounded-xl p-8 text-center text-slate-400">
            ${t('empty_categories_notice')}
          </div>
        `;
        return;
      }

      container.innerHTML = categories.map(cat => {
        const catSkills = skillsByCat[cat.category_id] || [];
        const isPenalty = cat.multiplier < 0 || cat.max_points < 0;
        const badgeBorder = isPenalty ? 'border-red-800 bg-red-950/60 text-red-300' : 'border-indigo-800 bg-indigo-950/60 text-indigo-300';
        const ptsUnit = (currentLang === 'ru') ? 'б.' : 'pts';
        const yrsUnit = (currentLang === 'ru') ? 'л.' : 'yrs';

        return `
          <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-2.5">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-sm font-bold text-white">${escapeHtml(cat.title)}</h3>
                <code class="text-[11px] px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 font-mono">${escapeHtml(cat.category_id)}</code>
                <span class="text-xs px-2 py-0.5 rounded-full border ${badgeBorder}">
                  ${t('cat_multiplier_label')} <strong>${cat.multiplier}x</strong>
                </span>
                <span class="text-xs px-2 py-0.5 rounded-full border border-slate-700 bg-slate-800 text-slate-300">
                  ${t('cat_limit_label')} <strong>${cat.max_points} ${ptsUnit}</strong>
                </span>
                <span class="text-xs px-2 py-0.5 rounded-full bg-slate-800/60 text-slate-400">
                  ${t('cat_skills_count_label')} <strong>${catSkills.length}</strong>
                </span>
              </div>
              <div class="flex items-center gap-1.5">
                <button onclick="openSkillModal('${escapeHtml(cat.category_id)}')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition" title="Add skill to this category">
                  ${t('btn_add_skill')}
                </button>
                <button onclick="openCategoryModal('${escapeHtml(cat.category_id)}')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium transition" title="Edit category parameters">
                  ${t('btn_edit')}
                </button>
                <button onclick="deleteCategory('${escapeHtml(cat.category_id)}')" class="px-2.5 py-1 rounded-lg bg-red-950/70 hover:bg-red-900 text-red-300 border border-red-800/60 text-xs transition" title="Delete category with all skills">
                  🗑️
                </button>
              </div>
            </div>

            <!-- Таблица навыков категории -->
            ${catSkills.length === 0 ? `
              <div class="text-xs text-slate-500 italic py-2">${t('empty_category_notice')}</div>
            ` : `
              <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                  <thead>
                    <tr class="text-slate-400 border-b border-slate-800 text-[11px] uppercase tracking-wider">
                      <th class="py-2 pr-3">${currentLang === 'ru' ? 'Навык' : 'Skill'}</th>
                      <th class="py-2 px-3 text-center" title="Experience in years">${currentLang === 'ru' ? 'Опыт (годы)' : 'Experience (yrs)'}</th>
                      <th class="py-2 px-3 text-center" title="Score points">${currentLang === 'ru' ? 'Баллы скоринга' : 'Score Points'}</th>
                      <th class="py-2 px-3 text-center">Primary</th>
                      <th class="py-2 px-3">${currentLang === 'ru' ? 'Синонимы / Алиасы' : 'Synonyms / Aliases'}</th>
                      <th class="py-2 pl-3 text-right">${currentLang === 'ru' ? 'Действия' : 'Actions'}</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-800/50">
                    ${catSkills.map(s => {
                      const aliasesStr = (s.aliases || []).join(', ');
                      const ptsColor = s.weight_points > 0 ? 'text-emerald-400' : (s.weight_points < 0 ? 'text-red-400' : 'text-slate-400');
                      return `
                        <tr class="hover:bg-slate-800/40 transition">
                          <td class="py-2 pr-3 whitespace-nowrap">
                            <div class="font-semibold text-slate-200">${escapeHtml(s.name)}</div>
                            <code class="text-[10px] text-slate-500 font-mono">${escapeHtml(s.skill_id)}</code>
                          </td>
                          <td class="py-2 px-3 text-center whitespace-nowrap">
                            <div class="flex items-center justify-center gap-1">
                              <input type="number" step="0.5" min="0" max="40"
                                id="years_${escapeHtml(s.skill_id)}"
                                value="${s.years_experience}"
                                oninput="onSkillYearsChange('${escapeHtml(s.skill_id)}', ${cat.multiplier}, ${cat.max_points})"
                                class="w-16 px-2 py-1 bg-slate-950 border border-slate-700 rounded text-center text-xs text-white focus:outline-none focus:border-indigo-500 font-mono" />
                              <span class="text-slate-500 text-[11px]">${yrsUnit}</span>
                            </div>
                          </td>
                          <td class="py-2 px-3 text-center whitespace-nowrap">
                            <div class="flex items-center justify-center gap-1">
                              <input type="number" step="1"
                                id="points_${escapeHtml(s.skill_id)}"
                                value="${s.weight_points}"
                                class="w-16 px-2 py-1 bg-slate-950 border border-slate-700 rounded text-center text-xs font-bold ${ptsColor} focus:outline-none focus:border-indigo-500 font-mono" />
                              <span class="text-slate-500 text-[11px]">${ptsUnit}</span>
                            </div>
                          </td>
                          <td class="py-2 px-3 text-center whitespace-nowrap">
                            <input type="checkbox"
                              id="primary_${escapeHtml(s.skill_id)}"
                              ${s.is_primary ? 'checked' : ''}
                              class="rounded bg-slate-950 border-slate-700 text-indigo-600 focus:ring-0 cursor-pointer" />
                          </td>
                          <td class="py-2 px-3">
                            <input type="text"
                              id="aliases_${escapeHtml(s.skill_id)}"
                              value="${escapeHtml(aliasesStr)}"
                              class="w-full min-w-[200px] px-2.5 py-1 bg-slate-950 border border-slate-700 rounded text-xs text-slate-300 focus:outline-none focus:border-indigo-500" />
                          </td>
                          <td class="py-2 pl-3 text-right whitespace-nowrap">
                            <div class="flex items-center justify-end gap-1.5">
                              <button onclick="quickSaveSkill('${escapeHtml(s.skill_id)}', '${escapeHtml(cat.category_id)}', '${escapeHtml(s.name)}')"
                                class="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition shadow"
                                title="Сохранить изменения этого навыка">
                                💾
                              </button>
                              <button onclick="deleteSkillItem('${escapeHtml(s.skill_id)}')"
                                class="px-2 py-1 rounded bg-red-950/80 hover:bg-red-900 text-red-300 border border-red-800/60 text-xs transition"
                                title="Удалить навык">
                                🗑️
                              </button>
                            </div>
                          </td>
                        </tr>
                      `;
                    }).join('')}
                  </tbody>
                </table>
              </div>
            `}
          </div>
        `;
      }).join('');
    }

    function onSkillYearsChange(skillId, multiplier, maxPoints) {
      const yearsEl = document.getElementById('years_' + skillId);
      const pointsEl = document.getElementById('points_' + skillId);
      if (!yearsEl || !pointsEl) return;
      const years = parseFloat(yearsEl.value) || 0.0;
      let pts;
      if (multiplier < 0) {
        pts = maxPoints;
      } else {
        pts = Math.min(Math.round(years * multiplier), maxPoints);
      }
      pointsEl.value = pts;
      pointsEl.className = pointsEl.className.replace(/text-(emerald|red|slate)-400/g, '');
      pointsEl.classList.add(pts > 0 ? 'text-emerald-400' : (pts < 0 ? 'text-red-400' : 'text-slate-400'));
    }

    async function quickSaveSkill(skillId, categoryId, skillName) {
      const yearsEl = document.getElementById('years_' + skillId);
      const pointsEl = document.getElementById('points_' + skillId);
      const primaryEl = document.getElementById('primary_' + skillId);
      const aliasesEl = document.getElementById('aliases_' + skillId);

      const years = parseFloat(yearsEl ? yearsEl.value : 0) || 0.0;
      const points = parseInt(pointsEl ? pointsEl.value : 0, 10);
      const isPrimary = primaryEl ? primaryEl.checked : false;
      const aliasesRaw = aliasesEl ? aliasesEl.value : '';
      const aliases = aliasesRaw.split(',').map(a => a.trim()).filter(Boolean);

      try {
        const res = await fetch('/api/skills/item', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            skill_id: skillId,
            category_id: categoryId,
            name: skillName,
            years_experience: years,
            weight_points: points,
            is_primary: isPrimary,
            aliases: aliases
          })
        });
        if (!res.ok) throw new Error('Ошибка сервера');
        showToast(`✅ Навык «${skillName}» сохранен (${years} л. → ${points} б.)`);
        loadSkillsMatrix();
      } catch (err) {
        showToast('Ошибка сохранения навыка: ' + err.message);
      }
    }

    let isEditingCategory = false;

    function openCategoryModal(catId = null) {
      isEditingCategory = !!catId;
      const modal = document.getElementById('categoryModal');
      const titleEl = document.getElementById('categoryModalTitle');
      const idEl = document.getElementById('modalCatId');
      const nameEl = document.getElementById('modalCatTitle');
      const multEl = document.getElementById('modalCatMultiplier');
      const maxEl = document.getElementById('modalCatMaxPoints');
      const sortEl = document.getElementById('modalCatSortOrder');

      if (catId) {
        titleEl.textContent = '✏️ Редактирование категории';
        const cat = (cachedSkillsMatrix.categories || []).find(c => c.category_id === catId);
        if (cat) {
          idEl.value = cat.category_id;
          idEl.disabled = true;
          nameEl.value = cat.title;
          multEl.value = cat.multiplier;
          maxEl.value = cat.max_points;
          sortEl.value = cat.sort_order;
        }
      } else {
        titleEl.textContent = '➕ Добавление новой категории';
        idEl.value = '';
        idEl.disabled = false;
        nameEl.value = '';
        multEl.value = 2.0;
        maxEl.value = 20;
        sortEl.value = (cachedSkillsMatrix.categories || []).length + 1;
      }
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function closeCategoryModal() {
      const modal = document.getElementById('categoryModal');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }

    async function saveCategoryFromModal() {
      const id = document.getElementById('modalCatId').value.trim();
      const title = document.getElementById('modalCatTitle').value.trim();
      const mult = parseFloat(document.getElementById('modalCatMultiplier').value) || 2.0;
      const maxP = parseInt(document.getElementById('modalCatMaxPoints').value, 10) || 20;
      const sortOrder = parseInt(document.getElementById('modalCatSortOrder').value, 10) || 0;

      if (!id || !title) {
        showToast('Укажите ID и название категории');
        return;
      }

      try {
        const res = await fetch('/api/skills/category', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            category_id: id,
            title: title,
            multiplier: mult,
            max_points: maxP,
            sort_order: sortOrder
          })
        });
        if (!res.ok) throw new Error('Ошибка сервера');
        closeCategoryModal();
        showToast(`✅ Категория «${title}» сохранена`);
        loadSkillsMatrix();
      } catch (err) {
        showToast('Ошибка сохранения: ' + err.message);
      }
    }

    async function deleteCategory(catId) {
      if (!confirm(`Удалить категорию «${catId}» и все входящие в неё навыки?`)) return;
      try {
        const res = await fetch(`/api/skills/category/${encodeURIComponent(catId)}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Ошибка при удалении');
        showToast(`Категория ${catId} удалена`);
        loadSkillsMatrix();
      } catch (err) {
        showToast('Ошибка: ' + err.message);
      }
    }

    function openSkillModal(catId = null, skillId = null) {
      const modal = document.getElementById('skillModal');
      const catSelect = document.getElementById('modalSkillCatSelect');
      const idEl = document.getElementById('modalSkillId');
      const nameEl = document.getElementById('modalSkillName');
      const yearsEl = document.getElementById('modalSkillYears');
      const pointsEl = document.getElementById('modalSkillPoints');
      const primEl = document.getElementById('modalSkillPrimary');
      const aliasesEl = document.getElementById('modalSkillAliases');

      catSelect.innerHTML = (cachedSkillsMatrix.categories || [])
        .map(c => `<option value="${escapeHtml(c.category_id)}">${escapeHtml(c.title)} (${c.multiplier}x, max ${c.max_points})</option>`)
        .join('');

      if (catId) catSelect.value = catId;

      idEl.value = '';
      idEl.disabled = false;
      nameEl.value = '';
      yearsEl.value = '2.0';
      primEl.checked = false;
      aliasesEl.value = '';
      onModalYearsInput();

      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function closeSkillModal() {
      const modal = document.getElementById('skillModal');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }

    function onModalCategoryChange() {
      onModalYearsInput();
    }

    function onModalYearsInput() {
      const catSelect = document.getElementById('modalSkillCatSelect');
      const yearsEl = document.getElementById('modalSkillYears');
      const pointsEl = document.getElementById('modalSkillPoints');
      const catId = catSelect.value;
      const cat = (cachedSkillsMatrix.categories || []).find(c => c.category_id === catId);
      const mult = cat ? cat.multiplier : 2.0;
      const maxP = cat ? cat.max_points : 20;
      const years = parseFloat(yearsEl.value) || 0;
      const pts = mult < 0 ? maxP : Math.min(Math.round(years * mult), maxP);
      pointsEl.value = pts;
    }

    async function saveSkillFromModal() {
      const catId = document.getElementById('modalSkillCatSelect').value;
      const skillId = document.getElementById('modalSkillId').value.trim();
      const name = document.getElementById('modalSkillName').value.trim();
      const years = parseFloat(document.getElementById('modalSkillYears').value) || 0;
      const points = parseInt(document.getElementById('modalSkillPoints').value, 10);
      const isPrimary = document.getElementById('modalSkillPrimary').checked;
      const aliases = document.getElementById('modalSkillAliases').value.split(',').map(s => s.trim()).filter(Boolean);

      if (!skillId || !name) {
        showToast('Укажите ID и название навыка');
        return;
      }

      try {
        const res = await fetch('/api/skills/item', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            skill_id: skillId,
            category_id: catId,
            name: name,
            years_experience: years,
            weight_points: points,
            is_primary: isPrimary,
            aliases: aliases
          })
        });
        if (!res.ok) throw new Error('Ошибка сервера');
        closeSkillModal();
        showToast(`✅ Навык «${name}» сохранен!`);
        loadSkillsMatrix();
      } catch (err) {
        showToast('Ошибка сохранения: ' + err.message);
      }
    }

    async function deleteSkillItem(skillId) {
      if (!confirm(`Удалить навык «${skillId}» из матрицы?`)) return;
      try {
        const res = await fetch(`/api/skills/item/${encodeURIComponent(skillId)}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Ошибка при удалении');
        showToast(`Навык ${skillId} удален`);
        loadSkillsMatrix();
      } catch (err) {
        showToast('Ошибка: ' + err.message);
      }
    }

    async function resetSkillsDefaults() {
      if (!confirm('Восстановить базовый набор категорий и навыков по умолчанию? Существующие категории и навыки будут дополнены базовыми.')) return;
      try {
        const res = await fetch('/api/skills/reset-defaults', { method: 'POST' });
        if (!res.ok) throw new Error('Ошибка при сбросе к базовым');
        const data = await res.json();
        showToast(`✅ Базовый набор восстановлен (${data.categories_count} категорий, ${data.skills_count} навыков)`);
        loadSkillsMatrix();
      } catch (err) {
        showToast('Ошибка: ' + err.message);
      }
    }

    let currentCvAnalysisData = null;

    async function handleCvPdfUpload(event) {
      const file = event.target.files && event.target.files[0];
      if (!file) return;

      event.target.value = '';

      if (!file.name.toLowerCase().endsWith('.pdf')) {
        showToast('Пожалуйста, выберите файл с расширением .pdf');
        return;
      }

      const overlay = document.getElementById('cvLoadingOverlay');
      if (overlay) {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
      }

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/candidate/upload-cv-pdf', {
          method: 'POST',
          body: formData
        });

        if (!res.ok) {
          let errMsg = `Ошибка сервера (${res.status})`;
          try {
            const errData = await res.json();
            if (typeof errData.detail === 'string') {
              errMsg = errData.detail;
            } else if (Array.isArray(errData.detail)) {
              errMsg = errData.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
            } else if (errData.detail) {
              errMsg = JSON.stringify(errData.detail);
            }
          } catch (_) {
            try {
              const text = await res.text();
              if (text) errMsg = text.slice(0, 150);
            } catch (_) {}
          }
          throw new Error(errMsg);
        }

        const data = await res.json();
        currentCvAnalysisData = data;
        openCvAnalysisModal(data);
      } catch (err) {
        showToast('Ошибка разбора резюме: ' + err.message);
      } finally {
        if (overlay) {
          overlay.classList.add('hidden');
          overlay.classList.remove('flex');
        }
      }
    }

    function openCvAnalysisModal(data) {
      const modal = document.getElementById('cvAnalysisModal');
      document.getElementById('cvModalFileBadge').textContent = data.filename || 'PDF Resume';
      document.getElementById('cvModalSummaryText').textContent = data.candidate_summary || 'Резюме распознано успешно.';
      document.getElementById('cvModalStructuredText').value = data.structured_cv || '';

      const diff = data.skills_diff || [];
      document.getElementById('cvModalSkillsCount').textContent = diff.length;

      const newCnt = diff.filter(s => s.status === 'new').length;
      const updCnt = diff.filter(s => s.status === 'updated').length;
      const unchCnt = diff.filter(s => s.status === 'unchanged').length;

      document.getElementById('cvCntNew').textContent = newCnt;
      document.getElementById('cvCntUpdated').textContent = updCnt;
      document.getElementById('cvCntUnchanged').textContent = unchCnt;

      renderCvDiffTable(diff);

      switchCvModalTab('skills');
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function closeCvAnalysisModal() {
      const modal = document.getElementById('cvAnalysisModal');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }

    function switchCvModalTab(tab) {
      const skillsTab = document.getElementById('cvModalTabSkills');
      const textTab = document.getElementById('cvModalTabText');
      const btnSkills = document.getElementById('cvTabBtnSkills');
      const btnText = document.getElementById('cvTabBtnText');

      if (tab === 'skills') {
        skillsTab.classList.remove('hidden');
        textTab.classList.add('hidden');
        btnSkills.className = 'px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-600 text-white';
        btnText.className = 'px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-400 hover:text-slate-200';
      } else {
        skillsTab.classList.add('hidden');
        textTab.classList.remove('hidden');
        btnSkills.className = 'px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-400 hover:text-slate-200';
        btnText.className = 'px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-600 text-white';
      }
    }

    function toggleSelectAllCvSkills(event) {
      const checked = event.target.checked;
      const tbody = document.getElementById('cvDiffTableBody');
      tbody.querySelectorAll('input[type="checkbox"].diff-chk').forEach(chk => {
        chk.checked = checked;
      });
    }

    function getCvAvailableCategories() {
      if (currentCvAnalysisData && Array.isArray(currentCvAnalysisData.available_categories) && currentCvAnalysisData.available_categories.length > 0) {
        return currentCvAnalysisData.available_categories;
      }
      if (cachedSkillsMatrix && Array.isArray(cachedSkillsMatrix.categories) && cachedSkillsMatrix.categories.length > 0) {
        return cachedSkillsMatrix.categories;
      }
      return [
        { category_id: "ai_agentic", title: "🤖 AI & Agentic Systems", multiplier: 15.0, max_points: 30 },
        { category_id: "core_backend", title: "☕ Core Backend & Languages", multiplier: 2.0, max_points: 20 },
        { category_id: "secondary_backend", title: "🐍 Secondary Languages / TS", multiplier: 3.0, max_points: 18 },
        { category_id: "arch_infra", title: "🏗️ Architecture & Cloud / DevOps", multiplier: 2.0, max_points: 15 },
        { category_id: "domains", title: "💼 Business Domains (FinTech / Banking)", multiplier: 2.0, max_points: 10 }
      ];
    }

    function renderCvPointsCellHtml(s) {
      const ptsUnit = (currentLang === 'ru') ? 'б.' : 'pts';
      if (s.status === 'new') {
        return `<span class="text-emerald-400 font-bold">+${s.new_points} ${ptsUnit}</span>`;
      } else if (s.status === 'updated') {
        return `<span class="text-slate-500 line-through mr-1">${s.old_points}</span><span class="text-blue-400 font-bold">➔ ${s.new_points} ${ptsUnit}</span>`;
      } else {
        return `<span class="text-slate-400">${s.new_points} ${ptsUnit}</span>`;
      }
    }

    function recalculateCvSkillRow(idx) {
      if (!currentCvAnalysisData || !currentCvAnalysisData.skills_diff) return;
      const s = currentCvAnalysisData.skills_diff[idx];
      if (!s) return;

      const catSelect = document.getElementById('cv_cat_' + idx);
      const yearsInput = document.getElementById('cv_years_' + idx);

      const selectedCid = catSelect ? catSelect.value : s.category_id;
      const selectedYears = yearsInput ? (parseFloat(yearsInput.value) || 0) : s.new_years;

      const cats = getCvAvailableCategories();
      const cat = cats.find(c => c.category_id === selectedCid) || {};
      const mult = parseFloat(cat.multiplier !== undefined ? cat.multiplier : 2.0);
      const maxP = parseInt(cat.max_points !== undefined ? cat.max_points : 20);

      let newPts = 0;
      if (mult < 0) {
        newPts = maxP;
      } else {
        newPts = Math.min(Math.round(selectedYears * mult), maxP);
      }

      s.category_id = selectedCid;
      s.category_title = cat.title || selectedCid;
      s.new_years = selectedYears;
      s.new_points = newPts;

      const cell = document.getElementById('cv_points_cell_' + idx);
      if (cell) {
        cell.innerHTML = renderCvPointsCellHtml(s);
      }
    }

    function onCvDiffCategoryChange(idx) {
      recalculateCvSkillRow(idx);
    }

    function onCvDiffYearsChange(idx) {
      recalculateCvSkillRow(idx);
    }

    function renderCvDiffTable(diff) {
      const tbody = document.getElementById('cvDiffTableBody');
      if (!tbody) return;

      if (!diff || diff.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-center text-slate-500 italic">${currentLang === 'ru' ? 'Навыки не распознаны' : 'No skills recognized'}</td></tr>`;
        return;
      }

      const availableCats = getCvAvailableCategories();
      const yrsUnit = (currentLang === 'ru') ? 'л' : 'y';

      tbody.innerHTML = diff.map((s, idx) => {
        let statusBadge = '';
        if (s.status === 'new') {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-semibold">${t('badge_cv_new')}</span>`;
        } else if (s.status === 'updated') {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800 text-[10px] font-semibold">${t('badge_cv_updated')}</span>`;
        } else {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 text-[10px]">${t('badge_cv_unchanged')}</span>`;
        }

        const isChecked = s.selected ? 'checked' : '';
        const aliasesStr = (s.aliases || []).join(', ');

        const catOptions = availableCats.map(cat => {
          const isSelected = (cat.category_id === s.category_id) ? 'selected' : '';
          return `<option value="${escapeHtml(cat.category_id)}" ${isSelected}>${escapeHtml(cat.title || cat.category_id)}</option>`;
        }).join('');

        return `
          <tr class="hover:bg-slate-900/60 transition ${s.status === 'unchanged' ? 'opacity-70' : ''}">
            <td class="py-2.5 px-2 text-center">
              <input type="checkbox" id="cv_chk_${idx}" data-idx="${idx}" class="diff-chk rounded bg-slate-950 border-slate-700 text-indigo-600 focus:ring-0 cursor-pointer" ${isChecked} />
            </td>
            <td class="py-2.5 px-2 whitespace-nowrap">
              ${statusBadge}
            </td>
            <td class="py-2.5 px-2">
              <div class="font-semibold text-white leading-tight">${escapeHtml(s.name)}</div>
              <select id="cv_cat_${idx}" onchange="onCvDiffCategoryChange(${idx})" class="mt-1 w-full max-w-[210px] px-1.5 py-0.5 rounded bg-slate-950 border border-slate-700 text-[11px] text-indigo-300 focus:outline-none focus:border-indigo-500 font-sans">
                ${catOptions}
              </select>
            </td>
            <td class="py-2.5 px-2 text-center whitespace-nowrap font-mono">
              <div class="flex items-center justify-center gap-1">
                ${s.status === 'updated' ? `<span class="text-slate-500 line-through text-[11px]">${s.old_years}${yrsUnit}</span>` : ''}
                <input type="number" step="0.5" min="0" max="40" id="cv_years_${idx}" value="${s.new_years}" onchange="onCvDiffYearsChange(${idx})" class="w-14 px-1 py-0.5 text-center bg-slate-950 border border-slate-700 rounded text-xs text-white focus:outline-none focus:border-indigo-500" />
              </div>
            </td>
            <td class="py-2.5 px-2 text-center whitespace-nowrap font-mono" id="cv_points_cell_${idx}">
              ${renderCvPointsCellHtml(s)}
            </td>
            <td class="py-2.5 px-2 text-center whitespace-nowrap">
              <input type="checkbox" id="cv_primary_${idx}" ${s.is_primary ? 'checked' : ''} class="rounded bg-slate-950 border-slate-700 text-indigo-600 focus:ring-0 cursor-pointer" />
            </td>
            <td class="py-2.5 px-2">
              <input type="text" id="cv_aliases_${idx}" value="${escapeHtml(aliasesStr)}" class="w-full min-w-[140px] px-2 py-0.5 bg-slate-950 border border-slate-800 rounded text-[11px] text-slate-300 focus:outline-none focus:border-indigo-500 font-mono" />
            </td>
          </tr>
        `;
      }).join('');
    }

    async function confirmApplyCvAnalysis() {
      if (!currentCvAnalysisData) return;

      const btn = document.getElementById('btnConfirmApplyCv');
      const origText = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Применение...';

      const updateCv = document.getElementById('applyOptUpdateCv').checked;
      const updateSkills = document.getElementById('applyOptUpdateSkills').checked;
      const updateProfile = document.getElementById('applyOptUpdateProfile').checked;
      const rescore = document.getElementById('applyOptRescore').checked;

      const structuredCvText = document.getElementById('cvModalStructuredText').value;

      const skillsToApply = [];
      const diff = currentCvAnalysisData.skills_diff || [];

      if (updateSkills) {
        diff.forEach((s, idx) => {
          const chk = document.getElementById('cv_chk_' + idx);
          if (chk && chk.checked) {
            const catSelect = document.getElementById('cv_cat_' + idx);
            const yearsInput = document.getElementById('cv_years_' + idx);
            const primChk = document.getElementById('cv_primary_' + idx);
            const aliasesInput = document.getElementById('cv_aliases_' + idx);
            const aliases = aliasesInput ? aliasesInput.value.split(',').map(a => a.trim()).filter(Boolean) : s.aliases;

            const selectedCid = catSelect ? catSelect.value : s.category_id;
            const selectedYears = yearsInput ? (parseFloat(yearsInput.value) || 0) : s.new_years;

            const cats = getCvAvailableCategories();
            const cat = cats.find(c => c.category_id === selectedCid) || {};
            const mult = parseFloat(cat.multiplier !== undefined ? cat.multiplier : 2.0);
            const maxP = parseInt(cat.max_points !== undefined ? cat.max_points : 20);
            const selectedPts = mult < 0 ? maxP : Math.min(Math.round(selectedYears * mult), maxP);

            skillsToApply.push({
              skill_id: s.skill_id,
              category_id: selectedCid,
              name: s.name,
              years_experience: selectedYears,
              weight_points: selectedPts,
              is_primary: primChk ? primChk.checked : s.is_primary,
              aliases: aliases
            });
          }
        });
      }

      try {
        const res = await fetch('/api/candidate/apply-cv-analysis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            update_cv_text: updateCv,
            structured_cv: structuredCvText,
            update_profile_text: updateProfile,
            candidate_summary: currentCvAnalysisData.candidate_summary,
            apply_skills: updateSkills,
            skills_to_apply: skillsToApply,
            rescore_jobs: rescore
          })
        });

        if (!res.ok) throw new Error('Ошибка сохранения на сервере');
        const respData = await res.json();

        closeCvAnalysisModal();

        let msg = '✅ Резюме успешно обработано!';
        if (respData.skills_applied > 0) msg += ` Применено ${respData.skills_applied} навыков.`;
        if (respData.rescored > 0) msg += ` Пересчитано ${respData.rescored} вакансий.`;
        showToast(msg);

        loadCandidateProfile();
        loadSkillsMatrix();
        if (respData.rescored > 0) loadJobs();

      } catch (err) {
        showToast('Ошибка применения данных: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = origText;
      }
    }

    // --- Синхронизация со скиллом @job-application-tracker и статусы ответов компаний в Applied ---
    let companyStageTarget = { job_id: null, company: null, title: null, stage: 'applied' };

    async function quickSetCompanyStage(jobId, stage, reason = null, emailUrl = null) {
      try {
        const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/application-stage`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            application_stage: stage,
            company_reject_reason: reason,
            application_email_url: emailUrl
          })
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        showToast(currentLang === 'ru' ? 'Статус ответа компании обновлён ✅' : 'Company response stage updated ✅');
        loadJobs();
      } catch (err) {
        showToast('Ошибка обновления статуса: ' + err.message);
      }
    }

    function fillGmailSearchLinkInModal() {
      const comp = (companyStageTarget.company || '').trim();
      const urlEl = document.getElementById('modalCompanyStageEmailUrlInput');
      if (!urlEl || !comp) return;
      urlEl.value = `https://mail.google.com/mail/u/0/#search/${encodeURIComponent('"' + comp + '"')}`;
    }

    function openCompanyStageModal(jobId, company, title, initialStage = 'applied', initialReason = '', initialEmailUrl = '') {
      companyStageTarget = {
        job_id: jobId,
        company: company || 'Unknown',
        title: title || jobId,
        stage: initialStage || 'applied'
      };
      const subEl = document.getElementById('modalCompanyStageSubtitle');
      if (subEl) subEl.textContent = `${title || jobId} @ ${company || 'Unknown'}`;
      const rsnEl = document.getElementById('modalCompanyStageReasonInput');
      if (rsnEl) rsnEl.value = initialReason || '';
      const urlEl = document.getElementById('modalCompanyStageEmailUrlInput');
      if (urlEl) {
        if (initialEmailUrl) {
          urlEl.value = initialEmailUrl;
        } else if (initialStage === 'interview' && company && company !== 'Unknown') {
          urlEl.value = `https://mail.google.com/mail/u/0/#search/${encodeURIComponent('"' + company + '"')}`;
        } else {
          urlEl.value = '';
        }
      }
      selectCompanyStageInModal(initialStage || 'applied');

      const modal = document.getElementById('companyStageModal');
      if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
      }
    }

    function closeCompanyStageModal() {
      const modal = document.getElementById('companyStageModal');
      if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
      }
    }

    function selectCompanyStageInModal(stage) {
      companyStageTarget.stage = stage;
      const styles = {
        applied: { active: 'border-indigo-500 bg-indigo-950/80 text-white font-semibold', inactive: 'border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500' },
        confirmed: { active: 'border-sky-500 bg-sky-950/80 text-sky-200 font-semibold', inactive: 'border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500' },
        interview: { active: 'border-emerald-500 bg-emerald-950/80 text-emerald-200 font-semibold', inactive: 'border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500' },
        rejected_by_company: { active: 'border-rose-500 bg-rose-950/80 text-rose-200 font-semibold', inactive: 'border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500' },
      };
      Object.entries(styles).forEach(([key, cls]) => {
        const btn = document.getElementById('stageBtn_' + key);
        if (btn) {
          btn.className = `px-3 py-2 rounded-lg border text-xs text-left transition ${stage === key ? cls.active : cls.inactive}`;
        }
      });
    }

    function setCompanyStageReasonPreset(text) {
      const rsnEl = document.getElementById('modalCompanyStageReasonInput');
      if (rsnEl) rsnEl.value = text;
    }

    async function confirmCompanyStageModal() {
      if (!companyStageTarget.job_id) return;
      const rsnEl = document.getElementById('modalCompanyStageReasonInput');
      const urlEl = document.getElementById('modalCompanyStageEmailUrlInput');
      const reason = rsnEl ? rsnEl.value.trim() : '';
      const emailUrl = urlEl ? urlEl.value.trim() : '';
      await quickSetCompanyStage(companyStageTarget.job_id, companyStageTarget.stage, reason || null, emailUrl || null);
      closeCompanyStageModal();
    }

    async function fetchTrackerPromptText() {
      const res = await fetch('/api/jobs/applied-tracker/prompt');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      return data.prompt || '';
    }

    async function copyTrackerPromptQuick() {
      try {
        const promptText = await fetchTrackerPromptText();
        await navigator.clipboard.writeText(promptText);
        showToast(currentLang === 'ru'
          ? '📋 Промпт для @job-application-tracker со списком компаний скопирован!'
          : '📋 @job-application-tracker prompt with your applied companies copied!');
      } catch (err) {
        showToast('Ошибка копирования промпта: ' + err.message);
      }
    }

    async function openTrackerSyncModal() {
      const modal = document.getElementById('trackerSyncModal');
      if (!modal) return;
      modal.classList.remove('hidden');
      modal.classList.add('flex');

      const hintEl = document.getElementById('trackerSyncStatusHint');
      if (hintEl) hintEl.textContent = '';

      try {
        const promptText = await fetchTrackerPromptText();
        const previewEl = document.getElementById('trackerPromptPreview');
        if (previewEl) previewEl.value = promptText;
      } catch (err) {
        console.error('Failed to load tracker prompt:', err);
      }
    }

    function closeTrackerSyncModal() {
      const modal = document.getElementById('trackerSyncModal');
      if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
      }
    }

    async function copyModalTrackerPrompt(openGemini = false) {
      const previewEl = document.getElementById('trackerPromptPreview');
      const text = previewEl && previewEl.value ? previewEl.value : await fetchTrackerPromptText();
      try {
        await navigator.clipboard.writeText(text);
        showToast(currentLang === 'ru'
          ? '📋 Запрос скопирован! Вставьте его в чат со скиллом в Gemini'
          : '📋 Query copied! Paste it into your Gemini chat');
        if (openGemini) {
          window.open('https://gemini.google.com/app', '_blank', 'noopener');
        }
      } catch (err) {
        showToast('Не удалось скопировать: ' + err.message);
      }
    }

    function renderTrackerSyncResults(data) {
      const box = document.getElementById('trackerSyncResultBox');
      const sumEl = document.getElementById('trackerSyncSummaryText');
      const cntEl = document.getElementById('trackerSyncCounters');
      const listEl = document.getElementById('trackerSyncUpdatesList');
      if (!box || !sumEl || !cntEl || !listEl) return;

      box.classList.remove('hidden');
      sumEl.textContent = data.summary || `Обновлено вакансий: ${data.updated_count || 0}`;
      const sc = data.stage_counts || {};
      cntEl.innerHTML = `
        <span class="px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800">📩 Подтверждено: <strong>${sc.confirmed || 0}</strong></span>
        <span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">🎤 Интервью: <strong>${sc.interview || 0}</strong></span>
        <span class="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">❌ Отказов: <strong>${sc.rejected_by_company || 0}</strong></span>
      `;

      const updates = data.updates || [];
      if (updates.length === 0) {
        listEl.innerHTML = `<div class="text-slate-400 italic py-1">${currentLang === 'ru' ? 'Совпадений с компаниями из раздела Applied не найдено.' : 'No matching companies found in Applied.'}</div>`;
        return;
      }

      listEl.innerHTML = updates.map(u => {
        let badge = `<span class="px-1.5 py-0.5 rounded bg-sky-900/80 text-sky-200 text-[11px]">📩 Подтверждено</span>`;
        if (u.stage === 'interview') {
          badge = `<span class="px-1.5 py-0.5 rounded bg-emerald-800 text-white font-semibold text-[11px]">🎤 HR / Интервью</span>`;
        } else if (u.stage === 'rejected_by_company') {
          badge = `<span class="px-1.5 py-0.5 rounded bg-rose-900/80 text-rose-200 text-[11px]">❌ Отказ</span>`;
        }
        return `
          <div class="p-2 rounded-lg bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-2">
            <div>
              <strong class="text-white">${escapeHtml(u.company || '')}</strong>
              <span class="text-slate-400"> • ${escapeHtml(u.title || u.job_id || '')}</span>
              ${u.reason ? `<div class="text-slate-300 mt-0.5">${escapeHtml(u.reason)}</div>` : ''}
            </div>
            <div class="flex items-center gap-2">
              ${u.email_url ? `<a href="${escapeHtml(u.email_url)}" target="_blank" rel="noopener" class="px-2 py-0.5 rounded bg-emerald-700 hover:bg-emerald-600 text-white text-[11px] font-semibold">✉️ Письмо ↗</a>` : ''}
              ${badge}
            </div>
          </div>
        `;
      }).join('');
    }

    async function executeTrackerSync(reportText) {
      const btnParse = document.getElementById('btnParseTrackerReport');
      const btnDirect = document.getElementById('btnTrackerDirectAgy');
      const hintEl = document.getElementById('trackerSyncStatusHint');
      if (btnParse) btnParse.disabled = true;
      if (btnDirect) btnDirect.disabled = true;
      if (hintEl) {
        hintEl.textContent = currentLang === 'ru'
          ? '⏳ ИИ сопоставляет компании и обновляет статусы в Applied...'
          : '⏳ AI is matching companies and updating Applied statuses...';
      }

      try {
        const res = await fetch('/api/jobs/applied-tracker/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            report_text: reportText || null,
            skill_name: '@job-application-tracker',
            apply_updates: true
          })
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || ('HTTP ' + res.status));
        }
        renderTrackerSyncResults(data);
        if (hintEl) {
          hintEl.textContent = `✅ Обновлено вакансий в базе: ${data.updated_count || 0}`;
        }
        showToast(`✅ Отмечено вакансий: ${data.updated_count || 0}`);
        loadJobs();
        fetchTrackerPromptText().then(newPrompt => {
          const previewEl = document.getElementById('trackerPromptPreview');
          if (previewEl) previewEl.value = newPrompt;
        }).catch(() => {});
      } catch (err) {
        if (hintEl) hintEl.textContent = '⚠️ ' + err.message;
        showToast('⚠️ ' + err.message, 5000);
      } finally {
        if (btnParse) btnParse.disabled = false;
        if (btnDirect) btnDirect.disabled = false;
      }
    }

    async function runTrackerSyncDirectAgy() {
      await executeTrackerSync(null);
    }

    async function runTrackerSyncFromModal() {
      const reportEl = document.getElementById('trackerReportInput');
      const reportText = reportEl ? reportEl.value.trim() : '';
      if (!reportText) {
        const hintEl = document.getElementById('trackerSyncStatusHint');
        const msg = currentLang === 'ru'
          ? '⚠️ Сначала вставьте в поле выше ответ от вашего скилла @job-application-tracker из веб-Gemini!'
          : '⚠️ Please paste the response from your @job-application-tracker skill in Web Gemini first!';
        if (hintEl) hintEl.textContent = msg;
        showToast(msg, 4500);
        if (reportEl) reportEl.focus();
        return;
      }
      await executeTrackerSync(reportText);
    }

    // --- Авто-обход всех систем (Макрос) и статусы времени последней проверки ---
    let cachedProviderChecks = {};
    let cachedMacroSettings = null;
    let draftMacroSteps = [];

    function formatHoursAgoBadge(info) {
      if (!info || !info.last_checked_at || info.hours_since === null || info.hours_since === undefined) {
        return {
          shortText: currentLang === 'ru' ? '🕒 не пров.' : '🕒 never',
          cls: 'text-[10px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-500 border border-slate-700/60 font-mono',
          tooltip: currentLang === 'ru' ? 'Ещё не проверялся' : 'Never checked yet'
        };
      }
      const hrs = Number(info.hours_since);
      let rel = '';
      if (hrs < 0.15) {
        rel = currentLang === 'ru' ? 'только что' : 'just now';
      } else if (hrs < 1) {
        const mins = Math.max(1, Math.round(hrs * 60));
        rel = currentLang === 'ru' ? `${mins}м назад` : `${mins}m ago`;
      } else if (hrs < 48) {
        rel = currentLang === 'ru' ? `${Math.round(hrs)}ч назад` : `${Math.round(hrs)}h ago`;
      } else {
        const days = Math.round(hrs / 24);
        rel = currentLang === 'ru' ? `${days}д назад` : `${days}d ago`;
      }

      let cls = 'text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/70 font-mono';
      if (hrs > 24) {
        cls = 'text-[10px] px-1.5 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/70 font-mono';
      } else if (hrs > 8) {
        cls = 'text-[10px] px-1.5 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/70 font-mono';
      }

      const tsClean = String(info.last_checked_at).replace('T', ' ').slice(0, 16) + ' UTC';
      const recH = info.recommended_hours_old || 8;
      const fetchedInfo = (info.fetched_count !== undefined && info.fetched_count !== null)
        ? (currentLang === 'ru' ? ` • Собрано: ${info.fetched_count}, прошло фильтр: ${info.matched_count || 0}` : ` • Fetched: ${info.fetched_count}, matched: ${info.matched_count || 0}`)
        : '';
      const tooltip = currentLang === 'ru'
        ? `Последняя проверка: ${tsClean} (${hrs}ч назад)${fetchedInfo} • Рекомендуемый Hours Old: ${recH}ч`
        : `Last checked: ${tsClean} (${hrs}h ago)${fetchedInfo} • Recommended Hours Old: ${recH}h`;

      return {
        shortText: `🕒 ${rel}`,
        cls,
        tooltip
      };
    }

    function renderProviderCheckBadges() {
      ['linkedin', 'indeed', 'glassdoor', 'hirify', 'upwork'].forEach(site => {
        const el = document.getElementById('lastCheck_' + site);
        if (!el) return;
        const info = cachedProviderChecks ? cachedProviderChecks[site] : null;
        const fmt = formatHoursAgoBadge(info);
        el.textContent = fmt.shortText;
        el.className = fmt.cls;
        el.title = fmt.tooltip;
      });
    }

    async function loadMacroAndProvidersStatus() {
      try {
        const res = await fetch('/api/pipeline/providers-status');
        if (!res.ok) return;
        const data = await res.json();
        if (data.provider_checks) {
          cachedProviderChecks = data.provider_checks;
          renderProviderCheckBadges();
          const curProvider = getSelectedProvider();
          const pInfo = cachedProviderChecks[curProvider];
          const hoursEl = document.getElementById('hoursOld');
          if (hoursEl && pInfo && pInfo.recommended_hours_old) {
            hoursEl.value = pInfo.recommended_hours_old;
          }
        }
        if (data.macro_settings) {
          cachedMacroSettings = data.macro_settings;
        }
      } catch (err) {
        console.error('Failed to load providers status:', err);
      }
    }

    async function startMacroPipeline(customSettings = null) {
      const termsRaw = document.getElementById('searchTerms').value;
      const searchTerms = termsRaw.split(',').map(s => s.trim()).filter(Boolean);

      const logContainer = document.getElementById('logContainer');
      if (logContainer) logContainer.classList.remove('hidden');
      const logOutput = document.getElementById('logOutput');
      if (logOutput) logOutput.textContent = '';
      logCursor = 0;
      updateLogButtonState(true);

      await fetch('/api/pipeline/start-macro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          search_terms: searchTerms,
          macro_settings: customSettings
        })
      });

      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(pollPipelineStatus, 1500);
      pollPipelineStatus();
    }

    const MACRO_SITE_LABELS = {
      hirify: { title: 'Hirify (IT & Digital Agent API)', icon: '🌐', badge: 'Единая база • Worldwide Remote' },
      upwork: { title: 'Upwork (Apify Actor API)', icon: '🟢', badge: 'Глобальный фриланс и контракты • Worldwide' },
      linkedin: { title: 'LinkedIn', icon: '💼', badge: 'Единая база • Макрорегионы EMEA + Worldwide' },
      indeed: { title: 'Indeed', icon: '🔍', badge: 'По региональным серверам-витринам • 100% Remote' },
      glassdoor: { title: 'Glassdoor', icon: '🏢', badge: 'По региональным серверам-витринам • Work From Home' }
    };

    async function openMacroSettingsModal() {
      const modal = document.getElementById('macroSettingsModal');
      if (!modal) return;

      try {
        const res = await fetch('/api/pipeline/macro-settings');
        if (res.ok) {
          const data = await res.json();
          if (data.provider_checks) {
            cachedProviderChecks = data.provider_checks;
            renderProviderCheckBadges();
          }
          if (data.macro_settings) {
            cachedMacroSettings = data.macro_settings;
          }
        }
      } catch (_) {}

      const ms = cachedMacroSettings || {
        execution_mode: 'per_provider',
        hours_mode: 'auto_from_last_run',
        default_hours_old: 8,
        max_auto_hours_old: 72,
        results_wanted: 50,
        llm_limit: 50,
        steps: [
          { site: 'hirify', enabled: true, hirify_mode: 'feeds', hirify_feed_id: 'all_active', locations: ['Worldwide'], countries: [] },
          { site: 'upwork', enabled: true, locations: ['Worldwide'], countries: [], easy_apply: false },
          { site: 'linkedin', enabled: true, locations: ['EMEA', 'Worldwide'], countries: [], easy_apply: false },
          { site: 'indeed', enabled: true, countries: ['uk', 'germany', 'netherlands'], locations: [], easy_apply: false },
          { site: 'glassdoor', enabled: false, countries: ['uk', 'germany'], locations: [], easy_apply: false }
        ]
      };

      const execRadio = document.querySelector(`input[name="macroExecMode"][value="${ms.execution_mode || 'per_provider'}"]`);
      if (execRadio) execRadio.checked = true;

      const hoursRadio = document.querySelector(`input[name="macroHoursMode"][value="${ms.hours_mode || 'auto_from_last_run'}"]`);
      if (hoursRadio) hoursRadio.checked = true;

      const defH = document.getElementById('macroDefaultHoursOld');
      if (defH) defH.value = ms.default_hours_old || 8;
      const maxH = document.getElementById('macroMaxAutoHoursOld');
      if (maxH) maxH.value = ms.max_auto_hours_old || 72;
      const rw = document.getElementById('macroResultsWanted');
      if (rw) rw.value = ms.results_wanted || 50;
      const ll = document.getElementById('macroLlmLimit');
      if (ll) ll.value = ms.llm_limit || 50;

      draftMacroSteps = JSON.parse(JSON.stringify(ms.steps || []));
      renderMacroStepsInModal();

      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function closeMacroSettingsModal() {
      const modal = document.getElementById('macroSettingsModal');
      if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
      }
    }

    function toggleMacroStepEnabled(idx) {
      if (!draftMacroSteps[idx]) return;
      draftMacroSteps[idx].enabled = !draftMacroSteps[idx].enabled;
      renderMacroStepsInModal();
    }

    function setMacroHirifyMode(idx, mode) {
      if (!draftMacroSteps[idx]) return;
      draftMacroSteps[idx].hirify_mode = mode;
      renderMacroStepsInModal();
    }

    function toggleMacroStepEasyApply(idx) {
      if (!draftMacroSteps[idx]) return;
      draftMacroSteps[idx].easy_apply = !draftMacroSteps[idx].easy_apply;
      renderMacroStepsInModal();
    }

    function toggleMacroStepLocation(idx, val, isCountry) {
      const step = draftMacroSteps[idx];
      if (!step) return;
      const field = isCountry ? 'countries' : 'locations';
      const arr = Array.isArray(step[field]) ? step[field] : [];
      const pos = arr.indexOf(val);
      if (pos >= 0) {
        if (arr.length > 1) {
          arr.splice(pos, 1);
        } else {
          showToast(currentLang === 'ru' ? 'Оставьте хотя бы одну локацию для системы' : 'Keep at least one location selected');
          return;
        }
      } else {
        arr.push(val);
      }
      step[field] = arr;
      renderMacroStepsInModal();
    }

    function renderMacroStepsInModal() {
      const container = document.getElementById('macroStepsContainer');
      if (!container) return;

      container.innerHTML = draftMacroSteps.map((step, idx) => {
        const site = step.site;
        const meta = MACRO_SITE_LABELS[site] || { title: site, icon: '🌐', badge: '' };
        const pCfg = PROVIDER_CONFIG[site] || PROVIDER_CONFIG.linkedin;
        const checkInfo = cachedProviderChecks ? cachedProviderChecks[site] : null;
        const fmt = formatHoursAgoBadge(checkInfo);
        const recHours = (checkInfo && checkInfo.recommended_hours_old) ? checkInfo.recommended_hours_old : (document.getElementById('macroDefaultHoursOld')?.value || 8);

        const isCountrySite = (site === 'indeed' || site === 'glassdoor');
        const selectedValues = isCountrySite
          ? (Array.isArray(step.countries) && step.countries.length ? step.countries : ['uk'])
          : (Array.isArray(step.locations) && step.locations.length ? step.locations : ['EMEA']);

        const showLocations = !(site === 'hirify' && (step.hirify_mode || 'feeds') === 'feeds');

        const chipsHtml = (pCfg.options || []).map(opt => {
          const isSel = selectedValues.includes(opt.value);
          const chipCls = isSel
            ? 'px-2.5 py-1 rounded-md text-xs font-semibold bg-violet-600 text-white border border-violet-400 shadow cursor-pointer transition'
            : 'px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 text-slate-400 border border-slate-700 hover:border-slate-500 hover:text-slate-200 cursor-pointer transition';
          return `<button type="button" onclick="toggleMacroStepLocation(${idx}, '${escapeJsArg(opt.value)}', ${isCountrySite})" class="${chipCls}">${escapeHtml(opt.label)}</button>`;
        }).join('');

        return `
          <div class="p-3.5 rounded-xl border transition ${step.enabled ? 'bg-slate-900/95 border-violet-700/60' : 'bg-slate-950/60 border-slate-800 opacity-60'} space-y-2.5">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex flex-wrap items-center gap-2.5">
                <label class="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input type="checkbox" ${step.enabled ? 'checked' : ''} onchange="toggleMacroStepEnabled(${idx})"
                    class="rounded bg-slate-950 border-slate-600 text-violet-600 focus:ring-0 w-4 h-4 cursor-pointer" />
                  <span class="text-sm font-bold text-white">${meta.icon} ${escapeHtml(meta.title)}</span>
                </label>
                <span class="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">${escapeHtml(meta.badge)}</span>
                <span class="${fmt.cls}" title="${escapeHtml(fmt.tooltip)}">${escapeHtml(fmt.shortText)}</span>
                <span class="text-[11px] text-violet-300 font-mono">→ авто: <strong>${recHours}ч</strong></span>
              </div>

              <div class="flex items-center gap-2">
                ${pCfg.supportsEasyApply ? `
                  <label class="inline-flex items-center gap-1.5 text-xs text-slate-300 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-700 cursor-pointer select-none">
                    <input type="checkbox" ${step.easy_apply ? 'checked' : ''} onchange="toggleMacroStepEasyApply(${idx})" class="rounded bg-slate-900 border-slate-600 text-indigo-600" />
                    <span>⚡ Easy Apply</span>
                  </label>
                ` : ''}
              </div>
            </div>

            ${site === 'hirify' ? `
              <div class="flex flex-wrap items-center gap-2 pt-1 text-xs">
                <span class="text-slate-400">Режим Hirify:</span>
                <button type="button" onclick="setMacroHirifyMode(${idx}, 'feeds')"
                  class="px-2.5 py-1 rounded-md text-xs font-medium border transition ${(step.hirify_mode || 'feeds') === 'feeds' ? 'bg-indigo-600 text-white border-indigo-400' : 'bg-slate-950 text-slate-400 border-slate-700'}">
                  🎯 Все активные фильтры (Feeds)
                </button>
                <button type="button" onclick="setMacroHirifyMode(${idx}, 'custom')"
                  class="px-2.5 py-1 rounded-md text-xs font-medium border transition ${step.hirify_mode === 'custom' ? 'bg-indigo-600 text-white border-indigo-400' : 'bg-slate-950 text-slate-400 border-slate-700'}">
                  🔍 По строке поиска и локациям
                </button>
              </div>
            ` : ''}

            ${showLocations ? `
              <div class="space-y-1.5 pt-1">
                <div class="text-[11px] text-slate-300">
                  ${isCountrySite
                    ? '🌐 <strong>Региональные серверы-витрины</strong> <span class="text-slate-400">(у этой площадки нет единого мирового сайта — скрипт собирает 100% Remote вакансии с выбранных доменов-хабов, а наш фильтр и ИИ оставляют только подходящие для удалёнки из Грузии / EMEA / Worldwide):</span>'
                    : '🌍 <strong>Охват поиска</strong> <span class="text-slate-400">(достаточно отметить <code>Worldwide</code> и <code>EMEA</code>, чтобы захватить всю глобальную удалёнку):</span>'}
                </div>
                <div class="flex flex-wrap gap-1.5">
                  ${chipsHtml}
                </div>
              </div>
            ` : `
              <div class="text-[11px] text-emerald-300/90 pt-0.5">
                🌍 В режиме <strong>Feeds</strong> Hirify сразу ищет глобальную удалёнку по всем вашим сохранённым фильтрам (дополнительные локации выбирать не нужно).
              </div>
            `}
          </div>
        `;
      }).join('');
    }

    function collectMacroSettingsFromModal() {
      const execRadio = document.querySelector('input[name="macroExecMode"]:checked');
      const hoursRadio = document.querySelector('input[name="macroHoursMode"]:checked');
      return {
        execution_mode: execRadio ? execRadio.value : 'per_provider',
        hours_mode: hoursRadio ? hoursRadio.value : 'auto_from_last_run',
        default_hours_old: parseInt(document.getElementById('macroDefaultHoursOld')?.value || '8', 10),
        max_auto_hours_old: parseInt(document.getElementById('macroMaxAutoHoursOld')?.value || '72', 10),
        results_wanted: parseInt(document.getElementById('macroResultsWanted')?.value || '50', 10),
        llm_limit: parseInt(document.getElementById('macroLlmLimit')?.value || '50', 10),
        steps: draftMacroSteps
      };
    }

    async function saveMacroSettingsFromModal(andRun = false) {
      const payload = collectMacroSettingsFromModal();
      try {
        const res = await fetch('/api/pipeline/macro-settings', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (data.macro_settings) cachedMacroSettings = data.macro_settings;
        if (data.provider_checks) {
          cachedProviderChecks = data.provider_checks;
          renderProviderCheckBadges();
        }
        closeMacroSettingsModal();
        if (andRun) {
          showToast(currentLang === 'ru' ? '⚡ Настройки сохранены, запускаем авто-обход систем...' : '⚡ Settings saved, starting macro pipeline...');
          await startMacroPipeline(cachedMacroSettings);
        } else {
          showToast(currentLang === 'ru' ? '💾 Настройки авто-обхода сохранены!' : '💾 Macro settings saved!');
        }
      } catch (err) {
        showToast('Ошибка сохранения настроек макроса: ' + err.message);
      }
    }

    applyLanguage();
    onProviderChange();
    loadMacroAndProvidersStatus();
    loadJobs();
    loadSkillsMatrix();
    pollPipelineStatus();
    updateLogButtonState();

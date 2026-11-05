    let currentTab = 'actionable';
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
        hide_log: "Hide Log",
        tab_actionable_text: "Actionable",
        tab_top_text: "Top Match ≥70",
        tab_good_text: "Good 50–69",
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
        toast_status_updated: "Status updated"
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
        hide_log: "Скрыть лог",
        tab_actionable_text: "Сухой остаток",
        tab_top_text: "Top Match ≥70",
        tab_good_text: "Good 50–69",
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
        toast_status_updated: "Статус обновлен"
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
        label: "Локация (LinkedIn)",
        remoteMechanism: "🔍 Ключевые слова в заголовке/локации: «Remote», «Work from Home», «WFH» (в гостевом API нет параметра f_WT=2)",
        hint: "LinkedIn: поддерживает макрорегионы (EMEA, EU, Worldwide) и страны; удалёнка ищется через слово Remote в запросе",
        supportsEasyApply: true,
        options: [
          { value: "EMEA", label: "🌍 EMEA (Европа, Ближний Восток, Африка)" },
          { value: "European Union", label: "🇪🇺 European Union" },
          { value: "Worldwide", label: "🌐 Worldwide (Весь мир)" },
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
        label: "Страна сервера (Indeed)",
        remoteMechanism: "🏷️ Системный атрибут GraphQL: Remote (DSQF7) + строгое исключение Hybrid (NOT PAXZC)",
        hint: "Indeed: аппаратный фильтр Remote по всей выбранной стране (слово Remote из запроса убирается автоматически)",
        supportsEasyApply: true,
        options: [
          { value: "uk", label: "🇬🇧 UK (uk.indeed.com)" },
          { value: "germany", label: "🇩🇪 Germany (de.indeed.com)" },
          { value: "netherlands", label: "🇳🇱 Netherlands (nl.indeed.com)" },
          { value: "poland", label: "🇵🇱 Poland (pl.indeed.com)" },
          { value: "spain", label: "🇪🇸 Spain (es.indeed.com)" },
          { value: "france", label: "🇫🇷 France (fr.indeed.com)" },
          { value: "ireland", label: "🇮🇪 Ireland (ie.indeed.com)" },
          { value: "switzerland", label: "🇨🇭 Switzerland (ch.indeed.com)" },
          { value: "portugal", label: "🇵🇹 Portugal (pt.indeed.com)" },
          { value: "czechrepublic", label: "🇨🇿 Czechia (cz.indeed.com)" },
          { value: "unitedarabemirates", label: "🇦🇪 UAE (ae.indeed.com)" },
          { value: "usa", label: "🇺🇸 USA (www.indeed.com)" },
          { value: "canada", label: "🇨🇦 Canada (ca.indeed.com)" }
        ]
      },
      glassdoor: {
        label: "Страна домена (Glassdoor)",
        remoteMechanism: "🏷️ Системный фильтр: remoteWorkType=1 (WORK_FROM_HOME) или локация «Remote»",
        hint: "Glassdoor: поддерживает только перечисленные страны с собственным доменом + фильтр Work From Home",
        supportsEasyApply: true,
        options: [
          { value: "uk", label: "🇬🇧 United Kingdom (glassdoor.co.uk)" },
          { value: "germany", label: "🇩🇪 Germany (glassdoor.de)" },
          { value: "netherlands", label: "🇳🇱 Netherlands (glassdoor.nl)" },
          { value: "france", label: "🇫🇷 France (glassdoor.fr)" },
          { value: "spain", label: "🇪🇸 Spain (glassdoor.es)" },
          { value: "ireland", label: "🇮🇪 Ireland (glassdoor.ie)" },
          { value: "switzerland", label: "🇨🇭 Switzerland (glassdoor.ch)" },
          { value: "austria", label: "🇦🇹 Austria (glassdoor.at)" },
          { value: "belgium", label: "🇧🇪 Belgium (glassdoor.be)" },
          { value: "italy", label: "🇮🇹 Italy (glassdoor.it)" },
          { value: "usa", label: "🇺🇸 United States (glassdoor.com)" },
          { value: "canada", label: "🇨🇦 Canada (glassdoor.ca)" }
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
      }
    };

    const SITE_REMOTE_BADGE_LABELS = {
      linkedin: "🏠 Remote / WFH",
      indeed: "🏠 Remote (DSQF7 • No Hybrid)",
      glassdoor: "🏠 Work From Home",
      hirify: "🌐 Agent API • Remote"
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
        { tab: 'actionable', countId: 'cntActionable', key: 'tab_actionable_text', icon: '🎯 ' },
        { tab: 'top', countId: 'cntTop', key: 'tab_top_text', icon: '🟢 ' },
        { tab: 'good', countId: 'cntGood', key: 'tab_good_text', icon: '🟡 ' },
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

    function openBadBoardModal(jobId, company, title, existingDomain = '') {
      modalTargetJob = { job_id: jobId, company: company, title: title };
      document.getElementById('modalJobSubtitle').textContent =
        `${title || jobId} @ ${company || 'Unknown'}`;
      document.getElementById('modalBadDomainInput').value = existingDomain || 'cims.com';
      const modal = document.getElementById('badBoardModal');
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function openBadBoardModalForLastOpened() {
      if (!cachedLastOpenedJob || !cachedLastOpenedJob.job_id) return;
      openBadBoardModal(
        cachedLastOpenedJob.job_id,
        cachedLastOpenedJob.company,
        cachedLastOpenedJob.title,
        'cims.com'
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
      const llmLimit = parseInt(document.getElementById('llmLimit').value || '15', 10);
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

      document.getElementById('logContainer').classList.remove('hidden');
      document.getElementById('logOutput').textContent = '';
      logCursor = 0;

      await fetch('/api/pipeline/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          search_terms: searchTerms,
          site_names: siteNames,
          location: location,
          country_indeed: countryIndeed,
          results_wanted: 25,
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

    async function pollPipelineStatus() {
      const res = await fetch(`/api/pipeline/status?since=${logCursor}`);
      const data = await res.json();
      const pre = document.getElementById('logOutput');
      if (data.logs && data.logs.length > 0) {
        pre.textContent += data.logs.join('\n') + '\n';
        pre.scrollTop = pre.scrollHeight;
        logCursor = data.next_index;
        loadJobs();
      }
      const badge = document.getElementById('pipelineBadge');
      if (!data.running) {
        badge.innerHTML = '✅ Пайплайн завершен';
        badge.className = 'text-xs font-medium text-emerald-400';
        clearInterval(pollTimer);
        pollTimer = null;
        loadJobs();
      } else {
        badge.innerHTML = '<span class="animate-ping inline-block w-2 h-2 rounded-full bg-indigo-400"></span> Выполняется пайплайн...';
        badge.className = 'text-xs font-medium text-indigo-400 flex items-center gap-1.5';
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

    function renderJobCard(job) {
      const e = job.enrichment || {};
      const sd = job.score_details || {};
      const score = job.score;
      const isTop = score !== null && score >= 70;
      const isGood = score !== null && score >= 50 && score < 70;

      const scoreBadgeClass = isTop ? 'badge-top' : isGood ? 'badge-good' : 'badge-low';
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
      const atsDomain = job.ats_domain || '';
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
                ${job.reject_reason ? `<span class="text-xs px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800">Причина: ${escapeHtml(job.reject_reason)}</span>` : ''}
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
              ${job.user_status !== 'rejected' ? `
                <button onclick="openRejectJobModal('${escapeJsArg(job.job_id)}', '${escapeJsArg(job.company)}', '${escapeJsArg(job.title)}', '${escapeJsArg(job.user_reject_reason || '')}')"
                  class="px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 text-xs font-medium transition"
                  title="${t('btn_not_fit_title')}">
                  ${t('btn_not_fit')}
                </button>
              ` : (job.user_status !== 'applied' ? `
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'new')"
                  class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition">
                  ${t('btn_return_new')}
                </button>
              ` : '')}
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

          ${job.user_reject_reason ? `
            <div class="mt-3 text-xs text-rose-200 bg-rose-950/40 border border-rose-800/60 rounded-lg px-3 py-2 flex items-center justify-between gap-2">
              <div>
                <strong>❌ ${t('user_reject_reason_label')}:</strong> ${escapeHtml(job.user_reject_reason)}
              </div>
              <button onclick="openRejectJobModal('${escapeJsArg(job.job_id)}', '${escapeJsArg(job.company)}', '${escapeJsArg(job.title)}', '${escapeJsArg(job.user_reject_reason)}')" class="text-xs text-rose-400 hover:text-rose-200 underline whitespace-nowrap">
                ${t('btn_edit_reason')}
              </button>
            </div>
          ` : ''}

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
          ${job.description ? `
            <details class="mt-3 pt-2 border-t border-slate-800/60 text-xs">
              <summary class="cursor-pointer text-slate-400 hover:text-slate-200 select-none">
                📄 Показать оригинальный текст вакансии
              </summary>
              <pre class="mt-2 p-3 rounded-lg bg-slate-950 text-slate-300 whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-y-auto">${escapeHtml(job.description)}</pre>
            </details>
          ` : ''}
        </article>
      `;
    }

    let cachedJobs = [];
    let cachedStats = {};

    function renderJobsList() {
      const container = document.getElementById('jobsList');
      if (!container) return;
      if (!cachedJobs || cachedJobs.length === 0) {
        const pendingCount = cachedStats.pending_llm || 0;
        const noJobsText = (currentLang === 'ru') ? 'В этой вкладке пока нет вакансий.' : 'No vacancies in this tab yet.';
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
      container.innerHTML = cachedJobs.map(renderJobCard).join('');
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
        setTxt('cntActionable', (s.top_match || 0) + (s.good_match || 0));
        setTxt('cntTop', s.top_match || 0);
        setTxt('cntGood', s.good_match || 0);
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

    applyLanguage();
    onProviderChange();
    loadJobs();
    loadSkillsMatrix();

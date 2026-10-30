    let currentTab = 'actionable';
    let pollTimer = null;
    let logCursor = 0;

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
      google: {
        label: "Регион поиска (Google Jobs)",
        remoteMechanism: "🔍 Поисковый модификатор «remote» + маркеры «remote» / «wfh» / «Anywhere» в карточке",
        hint: "Google Jobs: агрегирует вакансии из Greenhouse, Lever, Ashby и Workday",
        supportsEasyApply: false,
        options: [
          { value: "Europe", label: "🇪🇺 Europe" },
          { value: "United Kingdom", label: "🇬🇧 United Kingdom" },
          { value: "Germany", label: "🇩🇪 Germany" },
          { value: "Netherlands", label: "🇳🇱 Netherlands" },
          { value: "Poland", label: "🇵🇱 Poland" },
          { value: "Spain", label: "🇪🇸 Spain" },
          { value: "United States", label: "🇺🇸 United States" }
        ]
      },
      zip_recruiter: {
        label: "Регион (ZipRecruiter)",
        remoteMechanism: "🏷️ Параметр refine_by_location_type=only_remote (теги REMOTE / REMOTE_OPTIONAL)",
        hint: "ZipRecruiter: работает только по рынку США и Канады (фильтр only_remote)",
        supportsEasyApply: true,
        options: [
          { value: "Remote", label: "🇺🇸 All USA (Remote)" },
          { value: "United States", label: "🇺🇸 United States" },
          { value: "Canada", label: "🇨🇦 Canada" }
        ]
      },
      hellowork: {
        label: "Локация (HelloWork)",
        remoteMechanism: "🏷️ Параметр t=Complet → французский бейдж «Télétravail complet» (100% удалёнка)",
        hint: "HelloWork: французская база вакансий (фильтр Télétravail complet)",
        supportsEasyApply: false,
        options: [
          { value: "France", label: "🇫🇷 Вся Франция (Télétravail)" },
          { value: "Paris", label: "🇫🇷 Paris" },
          { value: "Lyon", label: "🇫🇷 Lyon" }
        ]
      },
      bayt: {
        label: "Страна (Bayt MENA)",
        remoteMechanism: "🏷️ Фильтр remote_working_type=1 (бейдж «Remote») + автоматическое вычитание всех Hybrid-вакансий",
        hint: "Bayt: вакансии Ближнего Востока и Персидского залива (MENA)",
        supportsEasyApply: true,
        options: [
          { value: "all", label: "🌴 All MENA Countries" },
          { value: "uae", label: "🇦🇪 UAE (All)" },
          { value: "Dubai, UAE", label: "🇦🇪 Dubai, UAE" },
          { value: "Abu Dhabi, UAE", label: "🇦🇪 Abu Dhabi, UAE" },
          { value: "saudi-arabia", label: "🇸🇦 Saudi Arabia" },
          { value: "qatar", label: "🇶🇦 Qatar" }
        ]
      }
    };

    const SITE_REMOTE_BADGE_LABELS = {
      linkedin: "🏠 Remote / WFH",
      indeed: "🏠 Remote (DSQF7 • No Hybrid)",
      glassdoor: "🏠 Work From Home",
      google: "🏠 Remote / WFH",
      zip_recruiter: "🏠 Only Remote",
      hellowork: "🏠 Télétravail complet",
      bayt: "🏠 Remote (No Hybrid)"
    };

    function getSelectedProvider() {
      const checked = document.querySelector('input[name="siteProvider"]:checked');
      return checked ? checked.value : 'linkedin';
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

    function copySnippet(key) {
      navigator.clipboard.writeText(SNIPPETS[key]);
      showToast('Скопировано в буфер обмена!');
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
    }

    async function saveCandidateProfile() {
      const profile_text = document.getElementById('profileTextInput').value;
      const cv_text = document.getElementById('cvTextInput').value;
      const res = await fetch('/api/candidate', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_text, cv_text })
      });
      const data = await res.json();
      const tsEl = document.getElementById('candidateUpdatedAt');
      tsEl.textContent = data.updated_at ? `Обновлено: ${data.updated_at.replace('T', ' ').slice(0, 19)} UTC` : '';
      showToast('Профиль и CV сохранены в базу данных jobs.db ✅');
    }

    function exportCandidateJson() {
      const payload = {
        profile: document.getElementById('profileTextInput').value,
        cv: document.getElementById('cvTextInput').value
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

    async function setJobStatus(jobId, status) {
      await fetch(`/api/jobs/${encodeURIComponent(jobId)}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_status: status })
      });
      showToast(status === 'applied' ? 'Отмечено как «Откликнулся» ✅' : 'Статус обновлен');
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
          enrich_only: enrichOnly
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
                ${job.apply_url ? `<a href="${escapeHtml(job.apply_url)}" target="_blank" rel="noopener" onclick="trackJobOpen('${escapeJsArg(job.job_id)}')" class="text-indigo-400 hover:underline font-mono">⚡ Прямой Apply URL ↗</a>` : ''}
                ${job.industry ? `<span>🏢 ${escapeHtml(job.industry)}</span>` : ''}
              </div>
            </div>

            <!-- Кнопки действий для заполнения откликов -->
            <div class="flex flex-wrap items-center gap-2">
              <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener" onclick="trackJobOpen('${escapeJsArg(job.job_id)}')"
                class="px-3.5 py-1.5 rounded-lg ${isBadBoard ? 'bg-red-900/70 hover:bg-red-800 text-red-200 border border-red-700' : 'bg-indigo-600 hover:bg-indigo-500 text-white'} text-xs font-semibold transition">
                ${isBadBoard ? '⚠️ Открыть (В чёрном списке) ↗' : '🔗 Открыть вакансию ↗'}
              </a>
              ${job.user_status !== 'applied' ? `
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'applied')"
                  class="px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition">
                  ✅ Откликнулся
                </button>
              ` : `
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'new')"
                  class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition">
                  ↩ Вернуть в новые
                </button>
              `}
              <button onclick="openBadBoardModal('${escapeJsArg(job.job_id)}', '${escapeJsArg(job.company)}', '${escapeJsArg(job.title)}', '${escapeJsArg(atsDomain)}')"
                title="Добавить джоб-борд и компанию в черный список (например, cims.com)"
                class="px-2.5 py-1.5 rounded-lg bg-red-950/50 hover:bg-red-900/80 text-red-300 border border-red-800/60 text-xs font-medium transition">
                ⛔ В черный список
              </button>
              ${job.user_status !== 'hidden' ? `
                <button onclick="setJobStatus('${escapeJsArg(job.job_id)}', 'hidden')"
                  class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-red-950/60 text-slate-400 hover:text-red-300 border border-slate-700 text-xs transition">
                  🗑️
                </button>
              ` : ''}
            </div>
          </div>

          ${fitSummary ? `
            <div class="mt-3 text-sm text-indigo-200 bg-indigo-950/40 border border-indigo-800/50 rounded-lg px-3 py-2">
              💡 <strong>Резюме-фит:</strong> ${escapeHtml(fitSummary)}
            </div>
          ` : ''}

          <!-- Совпавшие и недостающие навыки -->
          ${(matched.length > 0 || missing.length > 0) ? `
            <div class="mt-3 space-y-1.5 text-xs">
              ${matched.length > 0 ? `
                <div class="flex flex-wrap items-center gap-1.5">
                  <span class="text-slate-400 font-medium">✅ Совпало (${matched.length}):</span>
                  ${matched.map(s => `<span class="px-2 py-0.5 rounded chip-match font-mono">${escapeHtml(s)}</span>`).join('')}
                </div>
              ` : ''}
              ${missing.length > 0 ? `
                <div class="flex flex-wrap items-center gap-1.5">
                  <span class="text-slate-400 font-medium">⚠️ Не указано в резюме (${missing.length}):</span>
                  ${missing.map(s => `<span class="px-2 py-0.5 rounded chip-miss font-mono">${escapeHtml(s)}</span>`).join('')}
                </div>
              ` : ''}
            </div>
          ` : ''}

          ${breakdown ? `
            <div class="mt-2 text-xs text-slate-400 italic">
              📊 Скоринг детали: ${escapeHtml(breakdown)}
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

    async function loadJobs() {
      const res = await fetch(`/api/jobs?tab=${encodeURIComponent(currentTab)}`);
      const data = await res.json();
      const s = data.stats || {};

      document.getElementById('cntTotal').textContent = s.total_in_db || 0;
      document.getElementById('cntActionable').textContent = (s.top_match || 0) + (s.good_match || 0);
      document.getElementById('cntTop').textContent = s.top_match || 0;
      document.getElementById('cntGood').textContent = s.good_match || 0;
      document.getElementById('cntPending').textContent = s.pending_llm || 0;
      document.getElementById('cntApplied').textContent = s.applied || 0;
      document.getElementById('cntRejected').textContent = s.rejected || 0;
      if (s.bad_boards_count !== undefined) {
        document.getElementById('cntBadBoards').textContent = s.bad_boards_count;
      }
      if (data.last_opened_job) {
        cachedLastOpenedJob = data.last_opened_job;
        updateLastOpenedBanner(cachedLastOpenedJob);
      }

      const container = document.getElementById('jobsList');
      if (!data.jobs || data.jobs.length === 0) {
        container.innerHTML = `
          <div class="card rounded-xl p-10 text-center text-slate-400">
            <p class="text-base">В этой вкладке пока нет вакансий.</p>
            ${s.pending_llm > 0 ? `<p class="text-xs mt-2 text-indigo-400">В базе есть ${s.pending_llm} скачанных вакансий, ожидающих ИИ-разбора — нажми кнопку <strong>«🧠 Только ИИ»</strong> выше!</p>` : ''}
          </div>
        `;
        return;
      }

      container.innerHTML = data.jobs.map(renderJobCard).join('');
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
            Категории не найдены. Нажмите «➕ Добавить категорию», чтобы создать первую.
          </div>
        `;
        return;
      }

      container.innerHTML = categories.map(cat => {
        const catSkills = skillsByCat[cat.category_id] || [];
        const isPenalty = cat.multiplier < 0 || cat.max_points < 0;
        const badgeBorder = isPenalty ? 'border-red-800 bg-red-950/60 text-red-300' : 'border-indigo-800 bg-indigo-950/60 text-indigo-300';

        return `
          <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-2.5">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-sm font-bold text-white">${escapeHtml(cat.title)}</h3>
                <code class="text-[11px] px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 font-mono">${escapeHtml(cat.category_id)}</code>
                <span class="text-xs px-2 py-0.5 rounded-full border ${badgeBorder}">
                  Множитель: <strong>${cat.multiplier}x</strong>
                </span>
                <span class="text-xs px-2 py-0.5 rounded-full border border-slate-700 bg-slate-800 text-slate-300">
                  Лимит: <strong>${cat.max_points} б.</strong>
                </span>
                <span class="text-xs px-2 py-0.5 rounded-full bg-slate-800/60 text-slate-400">
                  Навыков: <strong>${catSkills.length}</strong>
                </span>
              </div>
              <div class="flex items-center gap-1.5">
                <button onclick="openSkillModal('${escapeHtml(cat.category_id)}')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition" title="Добавить навык в эту категорию">
                  ➕ Добавить навык
                </button>
                <button onclick="openCategoryModal('${escapeHtml(cat.category_id)}')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium transition" title="Редактировать параметры категории">
                  ✏️ Изменить
                </button>
                <button onclick="deleteCategory('${escapeHtml(cat.category_id)}')" class="px-2.5 py-1 rounded-lg bg-red-950/70 hover:bg-red-900 text-red-300 border border-red-800/60 text-xs transition" title="Удалить категорию со всеми навыками">
                  🗑️
                </button>
              </div>
            </div>

            <!-- Таблица навыков категории -->
            ${catSkills.length === 0 ? `
              <div class="text-xs text-slate-500 italic py-2">В этой категории пока нет навыков. Нажмите «➕ Добавить навык».</div>
            ` : `
              <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                  <thead>
                    <tr class="text-slate-400 border-b border-slate-800 text-[11px] uppercase tracking-wider">
                      <th class="py-2 pr-3">Навык</th>
                      <th class="py-2 px-3 text-center" title="Опыт в годах">Опыт (годы)</th>
                      <th class="py-2 px-3 text-center" title="Баллы, начисляемые вакансии при совпадении">Баллы скоринга</th>
                      <th class="py-2 px-3 text-center" title="Ключевой навык (Primary)">Primary</th>
                      <th class="py-2 px-3">Синонимы / Алиасы в тексте</th>
                      <th class="py-2 pl-3 text-right">Действия</th>
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
                              <span class="text-slate-500 text-[11px]">л.</span>
                            </div>
                          </td>
                          <td class="py-2 px-3 text-center whitespace-nowrap">
                            <div class="flex items-center justify-center gap-1">
                              <input type="number" step="1"
                                id="points_${escapeHtml(s.skill_id)}"
                                value="${s.weight_points}"
                                class="w-16 px-2 py-1 bg-slate-950 border border-slate-700 rounded text-center text-xs font-bold ${ptsColor} focus:outline-none focus:border-indigo-500 font-mono" />
                              <span class="text-slate-500 text-[11px]">б.</span>
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

    function renderCvDiffTable(diff) {
      const tbody = document.getElementById('cvDiffTableBody');
      if (!tbody) return;

      if (!diff || diff.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-center text-slate-500 italic">Навыки не распознаны</td></tr>`;
        return;
      }

      tbody.innerHTML = diff.map((s, idx) => {
        let statusBadge = '';
        if (s.status === 'new') {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-semibold">Новый</span>`;
        } else if (s.status === 'updated') {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800 text-[10px] font-semibold">Изменился</span>`;
        } else {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 text-[10px]">Без изм.</span>`;
        }

        const isChecked = s.selected ? 'checked' : '';
        const aliasesStr = (s.aliases || []).join(', ');

        return `
          <tr class="hover:bg-slate-900/60 transition ${s.status === 'unchanged' ? 'opacity-70' : ''}">
            <td class="py-2.5 px-2 text-center">
              <input type="checkbox" id="cv_chk_${idx}" data-idx="${idx}" class="diff-chk rounded bg-slate-950 border-slate-700 text-indigo-600 focus:ring-0 cursor-pointer" ${isChecked} />
            </td>
            <td class="py-2.5 px-2 whitespace-nowrap">
              ${statusBadge}
            </td>
            <td class="py-2.5 px-2 whitespace-nowrap">
              <div class="font-semibold text-white">${escapeHtml(s.name)}</div>
              <div class="text-[11px] text-indigo-400">${escapeHtml(s.category_title || s.category_id)}</div>
            </td>
            <td class="py-2.5 px-2 text-center whitespace-nowrap font-mono">
              ${s.status === 'new' ? `
                <span class="text-emerald-400 font-semibold">${s.new_years} л.</span>
              ` : s.status === 'updated' ? `
                <span class="text-slate-500 line-through mr-1">${s.old_years} л.</span>
                <span class="text-blue-400 font-semibold">➔ ${s.new_years} л.</span>
              ` : `
                <span class="text-slate-400">${s.new_years} л.</span>
              `}
            </td>
            <td class="py-2.5 px-2 text-center whitespace-nowrap font-mono">
              ${s.status === 'new' ? `
                <span class="text-emerald-400 font-bold">+${s.new_points} б.</span>
              ` : s.status === 'updated' ? `
                <span class="text-slate-500 line-through mr-1">${s.old_points}</span>
                <span class="text-blue-400 font-bold">➔ ${s.new_points} б.</span>
              ` : `
                <span class="text-slate-400">${s.new_points} б.</span>
              `}
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
            const primChk = document.getElementById('cv_primary_' + idx);
            const aliasesInput = document.getElementById('cv_aliases_' + idx);
            const aliases = aliasesInput ? aliasesInput.value.split(',').map(a => a.trim()).filter(Boolean) : s.aliases;

            skillsToApply.push({
              skill_id: s.skill_id,
              category_id: s.category_id,
              name: s.name,
              years_experience: s.new_years,
              weight_points: s.new_points,
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

    onProviderChange();
    loadJobs();
    loadSkillsMatrix();

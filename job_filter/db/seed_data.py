"""Единый источник дефолтных данных: категории и навыки матрицы скоринга, бан-домены ATS.

Используется при первом запуске (чистая БД), по кнопке «Сбросить к базовым»
и как резервная матрица, если БД недоступна.
"""

DEFAULT_SKILL_CATEGORIES: list[dict] = [
    {"category_id": "ai_agentic", "title": "🤖 AI & Agentic Systems", "multiplier": 15.0, "max_points": 30, "sort_order": 1},
    {"category_id": "core_backend", "title": "☕ Core Backend & Languages", "multiplier": 2.0, "max_points": 20, "sort_order": 2},
    {"category_id": "secondary_backend", "title": "🐍 Secondary Languages / TS", "multiplier": 3.0, "max_points": 18, "sort_order": 3},
    {"category_id": "arch_infra", "title": "🏗️ Architecture & Cloud / DevOps", "multiplier": 2.0, "max_points": 15, "sort_order": 4},
    {"category_id": "domains", "title": "💼 Business Domains (FinTech / Banking)", "multiplier": 2.0, "max_points": 10, "sort_order": 5},
    {"category_id": "alien", "title": "🚫 Чужой стек (Штрафы)", "multiplier": -1.0, "max_points": -20, "sort_order": 6},
    {"category_id": "legacy", "title": "🦖 Устаревший стек (Штрафы)", "multiplier": -1.0, "max_points": -30, "sort_order": 7},
]

DEFAULT_CANDIDATE_SKILLS: list[dict] = [
    {"skill_id": "langgraph", "category_id": "ai_agentic", "name": "LangGraph", "years_experience": 2.0, "weight_points": 30, "is_primary": 1, "aliases": ["langgraph", "langchain", "crewai", "koog"]},
    {"skill_id": "agentic", "category_id": "ai_agentic", "name": "AI Agents / Multi-Agent", "years_experience": 2.0, "weight_points": 30, "is_primary": 1, "aliases": ["agentic", "agentic ai", "ai agentic", "ai agents", "agents", "multi-agent", "multi agent", "a2a"]},
    {"skill_id": "rag", "category_id": "ai_agentic", "name": "RAG & Vector DB", "years_experience": 2.0, "weight_points": 20, "is_primary": 1, "aliases": ["rag", "embeddings", "vector db", "mem0", "memsearch"]},
    {"skill_id": "mcp", "category_id": "ai_agentic", "name": "MCP Protocol", "years_experience": 1.5, "weight_points": 20, "is_primary": 1, "aliases": ["mcp", "model context protocol"]},
    {"skill_id": "llm", "category_id": "ai_agentic", "name": "LLMs / GenAI / Prompt Engineering", "years_experience": 2.5, "weight_points": 25, "is_primary": 1, "aliases": ["llm", "llms", "genai", "generative ai", "prompt engineering", "claude", "openai", "anthropic", "gpt"]},
    {"skill_id": "langsmith", "category_id": "ai_agentic", "name": "LLM Observability", "years_experience": 1.5, "weight_points": 15, "is_primary": 0, "aliases": ["langsmith", "langfuse", "hivetrace"]},
    {"skill_id": "java", "category_id": "core_backend", "name": "Java", "years_experience": 10.0, "weight_points": 20, "is_primary": 1, "aliases": ["java", "jvm"]},
    {"skill_id": "kotlin", "category_id": "core_backend", "name": "Kotlin", "years_experience": 5.0, "weight_points": 20, "is_primary": 1, "aliases": ["kotlin", "kmp", "kotlin multiplatform"]},
    {"skill_id": "spring_boot", "category_id": "core_backend", "name": "Spring Boot", "years_experience": 8.0, "weight_points": 20, "is_primary": 1, "aliases": ["spring", "spring boot", "spring data", "spring security", "spring ai"]},
    {"skill_id": "ktor", "category_id": "core_backend", "name": "Ktor", "years_experience": 3.0, "weight_points": 15, "is_primary": 0, "aliases": ["ktor"]},
    {"skill_id": "python", "category_id": "secondary_backend", "name": "Python", "years_experience": 4.0, "weight_points": 18, "is_primary": 1, "aliases": ["python"]},
    {"skill_id": "typescript", "category_id": "secondary_backend", "name": "TypeScript / Node.js", "years_experience": 2.0, "weight_points": 9, "is_primary": 0, "aliases": ["typescript", "ts", "node", "nodejs", "node.js"]},
    {"skill_id": "microservices", "category_id": "arch_infra", "name": "Microservices & Distributed Systems", "years_experience": 8.0, "weight_points": 15, "is_primary": 1, "aliases": ["microservices", "distributed systems", "high-load", "high load", "system design"]},
    {"skill_id": "kafka", "category_id": "arch_infra", "name": "Kafka & Event-Driven", "years_experience": 6.0, "weight_points": 15, "is_primary": 1, "aliases": ["kafka", "event-driven", "event driven", "event driven architecture", "rabbitmq"]},
    {"skill_id": "postgresql", "category_id": "arch_infra", "name": "PostgreSQL / SQL", "years_experience": 8.0, "weight_points": 15, "is_primary": 1, "aliases": ["postgresql", "postgres", "sql", "oracle", "mssql"]},
    {"skill_id": "docker_k8s", "category_id": "arch_infra", "name": "Docker & Kubernetes", "years_experience": 6.0, "weight_points": 15, "is_primary": 1, "aliases": ["docker", "kubernetes", "k8s"]},
    {"skill_id": "aws_cloud", "category_id": "arch_infra", "name": "AWS / Cloud Native", "years_experience": 5.0, "weight_points": 15, "is_primary": 1, "aliases": ["aws", "google cloud", "gcp", "cloud architecture", "cloud native"]},
    {"skill_id": "rest_api", "category_id": "arch_infra", "name": "REST & OpenAPI", "years_experience": 8.0, "weight_points": 12, "is_primary": 0, "aliases": ["rest", "rest api", "restful", "openapi", "swagger"]},
    {"skill_id": "fintech", "category_id": "domains", "name": "FinTech & Banking / Payments", "years_experience": 5.0, "weight_points": 10, "is_primary": 1, "aliases": ["fintech", "banking", "payments", "billing", "trading", "brokerage", "financial services", "custody", "enterprise"]},
    {"skill_id": "alien_go", "category_id": "alien", "name": "Golang", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["go", "golang"]},
    {"skill_id": "alien_dotnet", "category_id": "alien", "name": "C# / .NET", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["c#", ".net", "dotnet"]},
    {"skill_id": "alien_cpp", "category_id": "alien", "name": "C++", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["c++"]},
    {"skill_id": "alien_rust", "category_id": "alien", "name": "Rust", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["rust"]},
    {"skill_id": "alien_ruby", "category_id": "alien", "name": "Ruby / Rails", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["ruby", "rails"]},
    {"skill_id": "alien_php", "category_id": "alien", "name": "PHP", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["php"]},
    {"skill_id": "alien_scala", "category_id": "alien", "name": "Scala", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["scala"]},
    {"skill_id": "legacy_1c", "category_id": "legacy", "name": "1C Enterprise", "years_experience": 0.0, "weight_points": -30, "is_primary": 0, "aliases": ["1c", "1с", "oscript"]},
    {"skill_id": "legacy_sap", "category_id": "legacy", "name": "SAP / ABAP", "years_experience": 0.0, "weight_points": -30, "is_primary": 0, "aliases": ["sap", "abap"]},
    {"skill_id": "legacy_cobol", "category_id": "legacy", "name": "Cobol / Pega / Salesforce", "years_experience": 0.0, "weight_points": -30, "is_primary": 0, "aliases": ["cobol", "salesforce", "mulesoft", "pega"]},
]

DEFAULT_BLACKLISTED_BOARDS: list[tuple[str, str]] = [
    ("cims.com", "iCIMS (cims.com) — невозможно нормально заполнить форму"),
    ("icims.com", "iCIMS (icims.com) — невозможно нормально заполнить форму"),
]


def default_skill_matrix() -> dict:
    """Возвращает копию дефолтной матрицы в формате API (/api/skills/matrix)."""
    return {
        "categories": [dict(c) for c in DEFAULT_SKILL_CATEGORIES],
        "skills": [{**s, "aliases": list(s["aliases"])} for s in DEFAULT_CANDIDATE_SKILLS],
    }

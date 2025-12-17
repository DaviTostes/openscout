from crewai import Agent, Task, LLM, Process, Crew
from crewai_tools import SerperDevTool

from models import ResumeAnalysis, JobSearchResults

llm = LLM(
    model="openai/gpt-5-nano",
)

def search_jobs(resume_text: str):
    analyze_resume_agent = Agent(
        role="Analisador de curriculo técnico",
        goal="extrair habilidades técnicas, nível de experiência e idiomas falados de currículos de desenvolvedores.",
        backstory=(
            "Você é um agente especializado em analisar currículos técnicos de desenvolvedores de software. "
            "Seu objetivo é extrair habilidades técnicas, nível de experiência e idiomas falados."
        ),
        llm=llm
    )
    
    analyze_resume_task = Task(
        description=(
            "Analise o seguinte currículo e extraia as informações solicitadas no formato JSON estrito."
            "Não inclua explicações ou texto adicional fora do objeto JSON."
            f"Currículo: {resume_text}"
        ),
        expected_output="JSON estrito com as chaves: experience_level, skills, languages.",
        agent=analyze_resume_agent,
        output_pydantic=ResumeAnalysis,
    )

    search_jobs_agent = Agent(
        role="Caçador de vagas tech",
        goal="Buscar vagas de tecnologia que correspondam às habilidades, experiência e localização do candidato.",
        backstory=(
            "Você é especialista em encontrar vagas de tecnologia no LinkedIn usando busca eficiente. "
            "Foque em vagas que realmente combinem com as habilidades técnicas do candidato. "
            "Priorize qualidade sobre quantidade."
        ),
        llm=llm,
        tools=[SerperDevTool()]
    )
    
    search_jobs_task = Task(
        description=(
            "Use as informações da análise do currículo (habilidades técnicas, nível de experiência e idiomas) "
            "para buscar vagas relevantes no LinkedIn. "
            "IMPORTANTE: Combine as SKILLS do candidato com os requisitos das vagas. "
            "Busque vagas que mencionem as principais tecnologias/linguagens do candidato. "
            "Filtre por nível de experiência apropriado (Junior/Pleno/Senior). "
            "Priorize vagas no Brasil e posições remotas globais. "
            "Retorne no mínimo 5 vagas relevantes. "
            "Necessario incluir o email de contato da vaga. "
        ),
        expected_output="JSON com array de vagas contendo título, empresa, localização, plataforma, nível requerido, requisitos e email de contato.",
        agent=search_jobs_agent,
        context=[analyze_resume_task],
        output_pydantic=JobSearchResults,
    )
    
    crew = Crew(
        agents=[analyze_resume_agent, search_jobs_agent],
        tasks=[analyze_resume_task, search_jobs_task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    return result

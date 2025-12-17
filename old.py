from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pypdf import PdfReader
from pydantic import BaseModel, Field
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime


class JobListing(BaseModel):
    """Represents a single tech job listing"""
    job_title: str = Field(..., description="The job title/position name")
    company: str = Field(..., description="The company offering the position")
    location: str = Field(..., description="Job location (Remote/Hybrid/Onsite and city/country)")
    platform: str = Field(..., description="The job platform where this was found")
    required_experience_level: str = Field(..., description="Required experience level for the position")
    key_requirements: list[str] = Field(default_factory=list, description="List of key technical requirements and skills")
    contact_email: str = Field(default="", description="Contact email for the job application if available")


class JobListings(BaseModel):
    """Collection of job listings"""
    jobs: list[JobListing] = Field(default_factory=list, description="List of all job listings found")


class JobApplicationEmail(BaseModel):
    """Personalized email for a job application"""
    job_title: str = Field(..., description="The job title being applied for")
    company: str = Field(..., description="The company name")
    recipient_email: str = Field(..., description="The contact email to send the application")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Full email body content in the candidate's language")


class JobApplicationEmails(BaseModel):
    """Collection of personalized job application emails"""
    emails: list[JobApplicationEmail] = Field(default_factory=list, description="List of personalized application emails")

reader = PdfReader("curriculo.pdf")
resume_text = "".join(page.extract_text() for page in reader.pages)

gemini_llm = LLM(
    model="gemini/gemini-2.5-flash-lite",
    temperature=0.1,  # Very low temperature for strict JSON output
    max_tokens=8192,
    max_retries=5,
    timeout=120,
)

analyze_resume_agent = Agent(
    role="Resume Analyzer",
    goal="Extract technical skills, experience level, location, and language information from resumes",
    backstory="You are a technical recruiter specialized in identifying technical skills, evaluating experience levels, and extracting candidate location and language information from developer resumes. You can recognize programming languages, frameworks, databases, cloud platforms, tools, methodologies, and accurately assess years of experience, seniority level, geographic location, and spoken languages.",
    llm=gemini_llm
)

analyze_resume_task = Task(
    description=f"""Analyze this resume and extract:

1. ALL technical skills including:
   - Programming languages (e.g., C#, Golang, Python)
   - Frameworks and libraries (e.g., Entity Framework, Gin, Gorm)
   - Databases (e.g., PostgreSQL, Firebase)
   - Cloud platforms (e.g., Azure)
   - Tools and technologies (e.g., Docker, Gitflow)
   - Development methodologies (e.g., Agile)

2. Professional experience analysis:
   - Total years of professional experience
   - Experience level (Junior: 0-2 years, Mid-Level: 2-5 years, Senior: 5-8 years, Lead/Staff: 8+ years)

3. Location information:
   - Extract the candidate's location (city and/or country) from contact info, address, or work history
   - Identify the country clearly

4. Language proficiency:
   - Extract all languages the candidate speaks (look for language sections, certifications, or mentions in the resume)
   - Include proficiency levels if mentioned

Resume: {resume_text}

Output the data as a JSON object matching this structure:
{{
  "experience_level": "Junior|Mid-Level|Senior|Lead",
  "years_of_experience": number,
  "skills": ["skill1", "skill2"],
  "location": "location",
  "country": "country",
  "languages": ["lang1", "lang2"]
}}""",
    expected_output="Pure JSON object only.",
    agent=analyze_resume_agent,
    output_pydantic=ResumeAnalysis,
)

search_jobs_agent = Agent(
    role="Tech Job Hunter",
    goal="Search and aggregate tech job vacancies from popular job sites that match the candidate's skills, experience, and location preferences",
    backstory="You are an expert tech job aggregator with deep knowledge of the best platforms for finding developer and tech positions worldwide. You specialize in searching LinkedIn, Indeed, Glassdoor, Stack Overflow Jobs, GitHub Jobs, AngelList/Wellfound, Remote.co, and We Work Remotely. You excel at finding relevant opportunities both locally and globally, including remote positions.",
    llm=gemini_llm,
    tools=[SerperDevTool(), ScrapeWebsiteTool()]
)

search_jobs_task = Task(
    description="""Search for tech job vacancies on popular job platforms that match the candidate's technical skills, experience level, and location from the previous task.

Focus on these top tech job sites:
- LinkedIn (jobs.linkedin.com)
- Indeed (indeed.com)
- Glassdoor (glassdoor.com)
- Stack Overflow Jobs (stackoverflow.com/jobs)
- GitHub Jobs (github.com/jobs)
- AngelList/Wellfound (wellfound.com)
- Remote.co (remote.co)
- We Work Remotely (weworkremotely.com)

IMPORTANT - Experience Level Filtering:
- Use the experience_level and years_of_experience from the previous task to filter appropriate positions
- For Junior level: search for Junior, Entry-Level, Associate positions
- For Mid-Level: search for Mid-Level, Intermediate, Software Engineer II/III positions
- For Senior: search for Senior, Staff, Principal positions
- For Lead: search for Lead, Staff, Principal, Engineering Manager positions

IMPORTANT - Location-Based Search Strategy:
- Use the candidate's COUNTRY and LOCATION from the previous task
- PRIORITIZE jobs in the candidate's country (combine country name with role keywords)
- Include jobs that mention the candidate's LANGUAGES (especially for international companies)
- ALSO include fully remote positions from other countries (these are globally accessible)
- Include hybrid/onsite positions from the candidate's city/country
- Consider including positions from neighboring countries or major tech hubs if relevant

Search Strategy:
1. First, search for positions in the candidate's country matching their skills and level
2. Then, search for fully remote positions (these can be from anywhere)
3. Match the SKILLS from the previous task with job requirements
4. Consider language requirements - prioritize jobs matching the candidate's languages
5. IMPORTANT: Try to extract contact emails from job postings when available (look for recruiter emails, HR contacts, or application emails)

Return job listings with: Job Title, Company, Location, Platform, Required Experience Level, Contact Email (if available), and Key Requirements.

Output the data as a JSON object matching this structure:
{{
  "jobs": [
    {{
      "job_title": "string",
      "company": "string",
      "location": "string",
      "platform": "string",
      "required_experience_level": "string",
      "key_requirements": ["req1", "req2"],
      "contact_email": "email or empty string"
    }}
  ]
}}""",
    expected_output="Pure JSON object with jobs array.",
    agent=search_jobs_agent,
    context=[analyze_resume_task],
    output_pydantic=JobListings,
)

email_writer_agent = Agent(
    role="Job Application Email Writer",
    goal="Create personalized, professional job application emails in the candidate's native language",
    backstory="You are an expert career coach and professional email writer with extensive experience in tech recruitment. You excel at crafting compelling, personalized job application emails that highlight the candidate's relevant skills and experience while maintaining a professional and authentic tone. You write fluently in multiple languages and adapt your writing style to match cultural expectations.",
    llm=gemini_llm
)

create_emails_task = Task(
    description="""Create personalized job application emails for each job listing from the previous task.

IMPORTANT Instructions:
- Use the candidate's LANGUAGES from the resume analysis task to determine the email language
- If the candidate speaks Portuguese, write emails in Portuguese
- If the candidate speaks English, write emails in English
- Match the language to the job location/country when appropriate
- Use the candidate's SKILLS and EXPERIENCE from the resume analysis to personalize each email
- Highlight the most relevant skills for each specific job's requirements
- Keep emails professional, concise (3-4 paragraphs), and enthusiastic
- Only create emails for jobs that have a contact_email provided

Email Structure:
1. **Subject Line**: Clear, professional, and specific to the job
2. **Opening**: Professional greeting and state the position you're applying for
3. **Body**:
   - Brief introduction highlighting years of experience and level
   - Mention 2-3 most relevant skills that match the job requirements
   - Express enthusiasm about the opportunity and company
   - Include a brief mention of location compatibility (if remote/local)
4. **Closing**: Professional sign-off with call to action

Tone: Professional, confident, but not overly formal. Show genuine interest.

Generate one email per job listing that has a contact email.

Output the data as a JSON object matching this structure:
{{
  "emails": [
    {{
      "job_title": "string",
      "company": "string",
      "recipient_email": "string",
      "subject": "string",
      "body": "multi-line email text"
    }}
  ]
}}""",
    expected_output="Pure JSON object with emails array.",
    agent=email_writer_agent,
    context=[analyze_resume_task, search_jobs_task],
    output_pydantic=JobApplicationEmails,
)

analyze_resume_crew = Crew(
    agents=[analyze_resume_agent, search_jobs_agent, email_writer_agent],
    tasks=[analyze_resume_task, search_jobs_task, create_emails_task],
    process=Process.sequential,
    verbose=True,
    max_rpm=10,  
)

result = analyze_resume_crew.kickoff()

resume_analysis: ResumeAnalysis = analyze_resume_crew.tasks[0].output.pydantic

print("\n" + "="*60)
print("RESUME ANALYSIS")
print("="*60)
print(f"Experience Level: {resume_analysis.experience_level}")
print(f"Years of Experience: {resume_analysis.years_of_experience}")
print(f"Location: {resume_analysis.location}")
print(f"Country: {resume_analysis.country}")
print(f"Languages: {', '.join(resume_analysis.languages)}")
print(f"\nTechnical Skills ({len(resume_analysis.skills)}):")
for skill in resume_analysis.skills:
    print(f"  • {skill}")

# Access job listings from the second task
job_listings: JobListings = analyze_resume_crew.tasks[1].output.pydantic

print("\n" + "="*60)
print(f"JOB LISTINGS - Found {len(job_listings.jobs)} opportunities")
print("="*60 + "\n")

for i, job in enumerate(job_listings.jobs, 1):
    print(f"{i}. {job.job_title}")
    print(f"   Company: {job.company}")
    print(f"   Location: {job.location}")
    print(f"   Platform: {job.platform}")
    print(f"   Experience: {job.required_experience_level}")
    if job.contact_email:
        print(f"   Contact: {job.contact_email}")
    print(f"   Requirements: {', '.join(job.key_requirements)}")
    print()

# Access application emails from the third task
application_emails: JobApplicationEmails = result.pydantic

print("\n" + "="*60)
print(f"PERSONALIZED APPLICATION EMAILS - Generated {len(application_emails.emails)} emails")
print("="*60 + "\n")

for i, email in enumerate(application_emails.emails, 1):
    print(f"{i}. APPLICATION FOR: {email.job_title} at {email.company}")
    print(f"   To: {email.recipient_email}")
    print(f"   Subject: {email.subject}")
    print(f"\n   Email Body:")
    print("   " + "-"*56)
    # Indent each line of the email body
    for line in email.body.split('\n'):
        print(f"   {line}")
    print("   " + "-"*56)
    print()

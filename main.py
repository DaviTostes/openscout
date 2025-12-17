import streamlit as st
import PyPDF2
import docx

from agents import search_jobs

st.set_page_config(
    page_title="OpenScout",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 OpenScout")
st.subheader("Encontre vagas de tecnologia personalizadas para seu perfil")
st.write("Envie seu currículo e encontraremos as melhores oportunidades tech para você.")
with st.expander("📖 Como funciona?"):
    st.write("""
    1. **Envie seu currículo** em formato PDF ou DOCX
    2. **Análise automática** de suas habilidades, experiência e idiomas
    3. **Busca personalizada** em múltiplas plataformas de emprego
    4. **Receba vagas** que combinam com seu perfil
    """)

uploaded_file = st.file_uploader(
    "📄 Envie seu currículo",
    type=["pdf", "docx"],
    help="Formatos aceitos: PDF ou DOCX"
)

if uploaded_file is not None:
    resume_text = ""

    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                resume_text += page.extract_text()
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            for paragraph in doc.paragraphs:
                resume_text += paragraph.text + "\n"
        else:
            st.error("Formato de arquivo não suportado.")
            resume_text = ""
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        resume_text = ""

    if resume_text:
        if st.button("🚀 Buscar Vagas", type="primary", use_container_width=True):
            with st.spinner("Analisando seu currículo e buscando vagas..."):
                try:
                    result = search_jobs(resume_text)

                    tab1, tab2 = st.tabs(["📊 Análise do Currículo", "💼 Vagas Encontradas"])

                    with tab1:
                        st.success("✅ Análise concluída!")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader("Nível de Experiência")
                            exp_lvl_text = f"`{result.tasks_output[0].pydantic.experience_level}`"
                            st.markdown(exp_lvl_text)

                            st.subheader("Idiomas")
                            langs_text = ", ".join([f"`{lang}`" for lang in result.tasks_output[0].pydantic.languages])
                            st.markdown(langs_text)

                        with col2:
                            st.subheader("Habilidades Técnicas")
                            skills_text = ", ".join([f"`{skill}`" for skill in result.tasks_output[0].pydantic.skills])
                            st.markdown(skills_text)

                    with tab2:
                        jobs = result.tasks_output[1].pydantic.jobs

                        if jobs:
                            st.success(f"✅ {len(jobs)} vagas encontradas!")

                            st.subheader("Filtros")
                            col1, col2 = st.columns(2)

                            with col1:
                                platforms = list(set([job.platform for job in jobs]))
                                selected_platform = st.selectbox("Plataforma", ["Todas"] + platforms)

                            with col2:
                                levels = list(set([job.required_experience_level for job in jobs]))
                                selected_level = st.selectbox("Nível", ["Todos"] + levels)

                            filtered_jobs = jobs
                            if selected_platform != "Todas":
                                filtered_jobs = [j for j in filtered_jobs if j.platform == selected_platform]
                            if selected_level != "Todos":
                                filtered_jobs = [j for j in filtered_jobs if j.required_experience_level == selected_level]

                            st.divider()

                            for i, job in enumerate(filtered_jobs, 1):
                                with st.container():
                                    col1, col2 = st.columns([3, 1])

                                    with col1:
                                        st.markdown(f"### {i}. {job.job_title}")
                                        st.write(f"**🏢 Empresa:** {job.company}")
                                        st.write(f"**📍 Localização:** {job.location}")

                                    with col2:
                                        st.write(f"**Plataforma:** {job.platform}")
                                        exp_lvl_text = f"`{job.required_experience_level}`"
                                        st.markdown(exp_lvl_text)

                                    st.write("**📋 Requisitos:**")
                                    reqs_text = ", ".join([f"`{req}`" for req in job.key_requirements])
                                    st.markdown(reqs_text)

                                    if job.contact_email:
                                        st.write(f"**✉️ Contato:** {job.contact_email}")

                                    st.divider()
                        else:
                            st.warning("Nenhuma vaga encontrada. Tente novamente mais tarde.")

                except Exception as e:
                    st.error(f"Erro ao processar: {str(e)}")
    else:
        st.warning("⚠️ Não foi possível extrair texto do arquivo. Verifique se o arquivo está correto.")
else:
    st.info("👆 Comece enviando seu currículo no formato PDF, TXT ou DOCX.")


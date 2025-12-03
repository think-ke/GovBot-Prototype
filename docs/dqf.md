# A Data Quality and Data Ethics Framework for AI Readiness in Kenya

**Report by Tech Innovators Network (THINK) Tank**

**April 2025**

## Table of contents

Foreword
Why We Need a Data Quality Framework
Principles of the DQF
How to Use the Data Quality Framework
The Six Dimensions of Data Quality
Next Steps: Advancing the DQF
Annex A : Supporting Research and Outputs

## Foreword

In this digital age, the power of data is not just in its volume, but in its conformity to facts. From informing public health decisions to enabling inclusive digital services, data is the cornerstone of informed governance, citizen trust, and technological progress. However, without integrity, data becomes a liability rather than an asset.

In response to the critical need for a unified, practical guide for data governance, we at the Tech Innovators Network (THINK) Tank, initiated the development of the Data Quality Framework (DQF) — a flexible, actionable, and context-aware framework designed to help institutions assess, manage, and improve data quality across sectors. Grounded in both global standards and local realities, the DQF was shaped through institutional partnerships, pilot evaluations, and feedback.

We now extend this framework as a strategic foundation for institutional data quality transformation. The findings from pilot audits, using datasets from Strathmore University, and field assessments confirm the urgent need for stronger documentation, standardized validation protocols, and governance structures.

This report presents the full scope of the framework, complemented by lessons learned during implementation, and clear recommendations for continuous improvement. The work was graciously sponsored by UK International Development, through the UK-Kenya AI Challenge, a program administered through the Africa Center for Technology Studies (ACTS).

## Why We Need a Data Quality Framework?

Despite Kenya’s growing reliance on data to power digital services, planning, and public accountability, significant quality issues persist. Some of the challenges highlighted that established the need of a clear data quality framework for better AI data included:

* **Unclear Data Provenance** - It is often difficult to establish who the real owner and source of the data is. For instance, after evaluation of the farmer datasets we discovered that the enumerators often did not clearly define whether respondents are farmers, farm workers, or other stakeholders—compromising contextual accuracy.
* **Inconsistent Validation** - Researchers use personal methods to validate data without centralized documentation or standardization.
* **Lack of Formal Agreements with Third-Party Data Providers** - often relying on downloaded text files without APIs or service-level assurances.
* **Regulatory reliance** - Projects often defer to university compliance instead of maintaining dedicated project-level regulatory audits.
* **Missing documentation for data cleaning, transformation, or verification process**

A DQF addresses these systemic gaps by creating a national level standard and toolset for:

* **Establishing data verification procedures**
* **Creating compliance-ready documentation**
* **Promoting inter-agency interoperability**

## Principles of the DQF

The Data Quality Framework shall seek to establish a series of tools, processes and procedures that can be used to achieve assurance of data quality. The principles provide a high level target of quality or ethics, that the framework wishes to achieve upon application. The principles are generally more agile, and can be established in consensus with users and/or practitioners. Upon review of the Report of the IC&DE Sectoral Working Group (2024), the Kenya National AI Strategy (2025), the Kenya National AI Principles (2025) and the (Draft) Kenya AI Code of Practice Standard (2025), we established the following data principles:

* **User-Centricity** - Data must meet the needs of its users.
* **Transparency** - Metadata, lineage, and transformations must be traceable.
* **Accountability** - Roles and responsibilities must be clearly defined and enforced.
* **Fitness-for-Purpose** - Data should be suitable for the context in which it is used.
* **Continuous Improvement** - Regular updates and audits are mandatory
* **Openness & Ethics** - Data must respect privacy, equity, and openness.

Practical data initiatives continue to highlight the importance of structured quality frameworks. For example, the Mozilla Common Voice project, to which THINK contributed as a local partner, demonstrates the importance of community-driven, multilingual dataset development. This effort focused on collecting high-quality voice data in Swahili and indigenous languages, reflects key DQF principles—especially openness, relevance, and ethical data collection. Similarly, Dr. Betsy Muriuki’s agricultural data research uncovered insight into how data fragmentation and undocumented validation methods limit the use of farmer-level data in planning and intervention. The need for a DQF would guarantee easier institutionalizing of ethical data practices and privacy protections.

## How to Use the Data Quality Framework

The Data Quality Framework (DQF) is designed for both flexibility and structure. It can be adopted across different institutional scales—from small data units to large ministries—while ensuring that all users benefit from a unified approach to data quality improvement.

To facilitate successful adoption, the DQF outlines a **Six-Phase Implementation Pathway**. Each phase represents a logical step in institutionalizing high-quality data practices, starting from internal assessment and culminating in system-wide integration and knowledge sharing.

**Six-Phase Implementation Pathway**

1.  **PHASE 1: READINESS & BASELINE ASSESSMENT**
2.  **PHASE 2: DEFINE QUALITY OBJECTIVES**
3.  **PHASE 3: ASSIGN STEWARDSHIP AND GOVERNANCE ROLES**
4.  **PHASE 4: CAPACITY BUILDING AND TOOL DEPLOYMENT**
5.  **PHASE 5: CONDUCT PILOTS & REFINE**
6.  **PHASE 6: DOCUMENTATION & KNOWLEDGE SHARING**

### PHASE 1: Readiness and Baseline Assessment

This initial phase establishes the foundational understanding of an institution's current data landscape.

**Key Actions**

* **Map core datasets**
    Identify datasets that are mission-critical, frequently used, or regulatory in nature.
* **Use the DQF Questionnaire and Audit Template**
    Assess current practices across data sourcing, verification, preparation, consent, privacy, and stewardship.
* **Diagnose challenges**
    Highlight inconsistencies, undocumented processes, lack of validation tools, or incomplete consent and privacy frameworks.
* **Categorize datasets by risk and sensitivity**
    Flag those requiring urgent quality interventions (e.g., datasets related to health, education, finance, or vulnerable populations).

**Outcome**

A comprehensive baseline report that informs strategic prioritization in Phase 2.

### PHASE 2: Define Quality Objectives

In this phase, institutions tailor the DQF principles and quality dimensions to their operational context and strategic goals.

**Key Actions**

* **Select quality indicators relevant to your datasets** (e.g., accuracy rate for survey data, timeliness for emergency response data).
* **Set realistic benchmarks for improvement** (e.g., reduce missing fields to <5% in the next quarter).
* **Align with mandates and policies** - Ensure data goals support legal obligations (Data Protection Act, sectoral regulations) and institutional mandates (e.g., service delivery targets, audit requirements).
* **Differentiate by dataset type** - Define objectives differently for operational datasets (requiring precision) and strategic datasets (requiring relevance).

**Outcome**

Customized quality improvement plans with clear, measurable goals.

### PHASE 3: Assign Stewardship and Governance Roles

Effective data quality management requires clear accountability and distributed leadership.

**Key Actions**

* **Designate data stewards for each major dataset or department.** These individuals are responsible for ensuring quality, documentation, and compliance.
* **Define roles and responsibilities clearly in data governance policies.**
* **Establish or strengthen a Data Governance Committee, chaired by a senior leader, to coordinate implementation across departments.**
* **Empower stewards with authority and resources to lead quality audits, training, and remediation efforts.**

**Outcome**

A governance structure that ensures continuity, oversight, and accountability in quality assurance.

### PHASE 4: Capacity Building and Tool Deployment

This phase focuses on equipping staff and systems with the technical and human capabilities required to maintain data quality.

**Key Actions**

* Train institutional staff and stewards using the DQF training manual, online learning modules, and facilitated workshops.
* Deploy validation tools and scripts in data pipelines (e.g., automated checks for missing values, duplications, or outliers using tools like R or Python).
* Customize templates for metadata documentation, consent forms, data verification logs, and quality scorecards.
* Establish feedback loops for teams to report issues, suggest improvements, and monitor progress over time.

**Outcome**

A technically equipped workforce and an operational system capable of real-time and retrospective data validation.

## The Six Dimensions of Data Quality

Data quality characteristics:

* **Validity:** Is the data formatted correctly?
* **Consistency:** Does the data match across systems?
* **Completeness:** Is all the data present?
* **Accuracy:** Are the data points correct?
* **Timeliness:** Is the data up-to-date?
* **Uniqueness:** Are there any duplicates?

## Next Steps: Advancing the DQF

## Annex A : Supporting Research and Outputs

## PHASE 5: Conduct Pilots & Refine

Testing the framework in real operational environments helps reveal practical insights and refine approaches before full-scale rollout.

**Key Actions**

* Select high-priority sectors for piloting—such as agriculture, health, education, or social protection.
* Implement the DQF across a full data lifecycle, from collection and preprocessing to use and archiving.
* Document pilot findings, including data quality improvements, challenges faced, and feedback from users and data consumers.
* Refine tools and procedures based on real-world experiences (e.g., simplifying checklists, adjusting frequency of audits).

**Outcome**

Field-tested improvements and validated adaptations that make the framework more robust and scalable.

## PHASE 6: Documentation and Knowledge Sharing

Capturing and sharing institutional learning is vital for building a culture of continuous improvement and sectoral coherence.

**Key Actions**

* Publish institutional data quality reports or case studies for internal governance and public accountability.
* Share success stories and challenges at cross-sectoral forums, peer exchanges, or with the NDQAC (National Data Quality Assurance Committee).
* Institutionalize lessons learned by updating SOPs, integrating new practices into onboarding and training, and revising data management policies.

**Outcome**

A knowledge-driven culture where quality improvement is iterative, evidence-based, and widely disseminated.

## Six Dimensions of Data Quality

The DQF outlines six key dimensions of data quality. Each dimension captures a vital aspect of data performance and reliability. The combined application of these dimensions allows institutions to diagnose, monitor, and improve the quality of data in a systematic way.

### 1. Accuracy

**Definition:** The extent to which data correctly reflects the real-world values or events it is intended to represent.

**Why does it matter?** Inaccurate data can lead to misinformed decisions, policy failures, and mistrust from the public.

**Indicators:**

* Error rates (e.g., incorrect ID numbers, misspelled names)
* Validation against source data
* Frequency of manual correction

### 2. Completeness

**Definition:** The extent to which all required data is present and recorded without gaps.

**Why does it matter?** Incomplete data leads to poor analytical outcomes and underrepresentation. In public health, for instance, missing vaccination data could affect outbreak predictions and response.

**Indicators:**

* Percentage of blank or null fields
* Missing records in time-series datasets

### 3. Consistency

**Definition:** The extent to which data is presented in a uniform and logical format across datasets and systems.

**Why it matters** - Inconsistent data leads to duplication, inefficiencies, and conflict in policy implementation.

**Indicators:**

* Use of standard formats (e.g., date/time)
* Duplication rates
* Alignment across interoperable systems

### 4. Timeliness

**Definition:** The extent to which data is available and up-to-date when needed.

**Why it matters**

Late data leads to missed opportunities. Real-time or near-real-time data is critical in fast-moving sectors like agriculture (e.g., rainfall data), health (e.g., disease outbreaks), or emergency response.

**Indicators:**

* Time lag between event and data entry/publication
* Data refresh rates
* Availability of real-time feeds or APIs

### 5. Accessibility

**Definition:** The ease with which data can be retrieved and used by authorized stakeholders.

**Why it matters** - Even high-quality data loses value if it’s locked away or requires excessive effort to access. Accessibility is essential for transparency.

**Indicators:**

* Availability through APIs, dashboards, or open portals
* Licensing and reuse policies
* Documentation and metadata availability

### 6. Relevance

**Definition:** The extent to which data meets the needs of users and supports its intended purpose.

**Why it matters** - Collecting high volumes of data is not enough—it must serve a clear purpose. Irrelevant data wastes resources and leads to analytic overload.

**Indicators:**

* Stakeholder satisfaction surveys
* Alignment with decision-making requirements
* Demand vs. usage metrics

## Next Steps: Advancing the DQF

1.  **Standardize Third-Party Data Agreements**
    * Develop API-based data sourcing with embedded Service Level Agreements (SLAs).

2.  **Integrate a TFGbV Lexicon**
    * Integrate machine-readable terms into DQF-compliant datasets to support real-time detection.

3.  **Train Institutional Stewards**
    * Establish certification pathways in collaboration with Strathmore and Maseno.

4.  **Embed DQF in Digital Platforms**
    * Possibly align the framework with e-citizen and GovStack architectures

## Annex A : Supporting Research and Outputs

To complement the development of the DQF, this report includes relevant research outputs and practical demonstrations of the data quality focused innovation.

### Annex A.1: White Paper Contribution

**Title: The Impact of Audio Compression on Downstream Speech Processing Tasks**

As part of the foundational research that informed the DQF, a white paper authored by Nick Mumero (THINK) is attached.

This white paper provides an in-depth technical analysis of how audio compression formats—particularly MP3—affect the performance of speech processing tasks such as Automatic Speech Recognition (ASR), Text-to-Speech (TTS), and Speech-to-Text (STT).

**Key Findings**

* High intelligibility (STOI: 0.9893) and excellent perceptual quality (PESQ: 4.53)
* Minimal temporal smearing and phase degradation
* Compression is generally suitable for ASR, TTS, and STT—but care must be taken with high-frequency content loss.

**Relevance to DQF**

The white paper reinforces two DQF quality dimensions:

* **Accuracy** - Demonstrates how minor data alterations affect downstream outcomes.
* **Relevance** - Highlights how seemingly acceptable data formats may reduce task-specific model performance.

### Annex A.2: Case Study - Mozilla Common Voice (Swahili & Indigenous Languages)

As a supporting partner, Tech Innovators Network (THINK) contributed to the Mozilla Common Voice project in Kenya, focusing on the collection and validation of voice samples in Swahili. The goal of the project was to build open-source, publicly accessible datasets that can support more inclusive and linguistically diverse AI systems—especially in voice interfaces and speech recognition.

**THINK supported:**

* Community mobilization and recording sessions in underrepresented regions
* Data quality checks and validation feedback loops
* Promoting the ethical use of voice data with informed consent and documentation

This initiative aligns closely with DQF principles such as User-Centricity, Transparency, Openness, and Relevance—proving that ethical, collaborative data projects can meaningfully influence the design of AI systems and public digital tools.

## Project Partners & Contributors

This project was executed with input and collaboration from distinguished experts and institutions:

**Brian Omwenga**

Brian is an AI and Technology Policy Expert. The founder of Tech Innovators Network (THINK) is focused on the development of a strong and inclusive ICT ecosystem in Africa. After graduating from Strathmore and Massachusetts Institute of Technology (MIT) he has worked fruitfully in the private and the public sector. As a software engineer and project manager at Nokia he successfully started his journey of creating notable inventions and filing patents.
In the public sector he successfully designed a Government Wide Enterprise Architecture covering the business, data, applications and technology domains. As a result of these experiences, he champions the open innovation philosophy through collaboration, inclusiveness and quality output. He is extremely passionate about the role and power of COMMUNITY in the context of the ICT ecosystem.

**Dr. Betsy Muriuki - Strathmore University**

Dr. Betsy Muriithi is a Research Fellow at @iLabAfrica, where she leverages her expertise in data analytics to address pressing societal challenges. Her research focuses on using artificial intelligence (AI) technologies to drive sustainable development, particularly in agriculture and public health. Her current interests include exploring how these technologies can be used to create practical solutions for communities and businesses. She has developed tools that integrate AI and IoT to support smallholder farmers in enhancing climate resilience and productivity, as well as decision-support systems that allow human-computer interaction focusing on:
(1) the mechanisms that enable effective data use for decision-making—whether it's helping farmers optimize agricultural practices or assisting healthcare managers in boosting facility efficiency, and
(2) how AI and data systems can be designed to be more inclusive, fostering equitable access to technology in communities and businesses.

## Project Partners & Contributors (Continued)

**Monica Okoth - Kenya Bureau of Standards (KEBS)**

Monica Okoth is the Assistant Manager, ICT and Electrotechnical Department, Standards Development Division at the Kenya Bureau of Standards (KEBS). She serves as Technical Committee (TC) Manager for several national committees on topics related to AI, IT, and related technology.

Monica is also the National Committee Manager for the Joint International Technical Committee for Information Technology (ISO IEC JTC1). This involves developing national and international standards on software engineering, artificial intelligence, data centers, e-learning, IT service management, and IT governance. She has participated in developing several national policies including the National AI Strategy, e-waste regulations, energy efficiency standards, national communications, and assistive technology accessibility policies.

Monica is a certified Information Security Implementor and Auditor. She holds a bachelor's degree in Mathematics and Geography from the University of Nairobi and is pursuing a postgraduate certificate in Applied Statistics.

**Nick Mumero**

Nick is the AI Architect and Lead AI Engineer at THINK, where he oversees AI/ML teams and project delivery. He specializes in multilingual NLP and LLM applications, having led chatbot projects across public and private sectors. 

At THINK, Nick developed the top-performing Swahili ASR model using Wav2Vec 2.0 and built multilingual chatbots serving over 15,000 users monthly. He also created SHINJI, a low-resource smart speaker for English, Swahili, and Kikuyu. Nick has contributed to open-source Swahili models and published research on sentiment analysis, combining deep technical expertise with strong product leadership.

**Angela Kanyi**

Angela is an experienced software engineer and project manager. At THINK, she leads DevOps operations, managing collaborations between the developer team and users. Angela was integral in designing the Conformity Assessment Process (CAP) at THINK, which ensures all projects conform to high-quality standards throughout the software development lifecycle.

As the primary liaison between users and developers, Angela ensures smooth communication and delivers user-centric solutions. She has successfully managed projects serving over 5,000 users while at THINK. Her technical skills include JavaScript, React, DevOps tools, CI/CD, cloud infrastructure, and REST APIs. Angela possesses excellent knowledge of developer operations tools and user management solutions. Her strong communication skills have enabled her to be an effective problem-solver, communicator, and collaborator.

## Conclusion

The Data Quality Framework (DQF) represents a crucial step toward improving data governance across sectors.

The framework addresses systemic data quality gaps through practical, flexible, and context-aware principles. Pilot projects, like those at Maseno and Strathmore University, have highlighted the importance of standardized validation and documentation processes, emphasizing the need for robust governance structures. Moving forward, the DQF will be key in advancing data quality practices across institutions, with continued focus on training, tool deployment, and knowledge sharing.

As data becomes ever more central to decision-making, the DQF provides a strategic foundation for ensuring its integrity, relevance, and impact.

**GovBot: AI Conversational Chatbot for Discoverability of Government Services \[Case of Kenya]**


# ********

# **Product Use Case Summary**

|                   |                                                                |
| ----------------- | -------------------------------------------------------------- |
| ID                |                                                                |
| Name:             | GovBot - AI Chatbot for Discoverability of Government Services |
| Sector:           | Digital Government (eGovernment), Public Service Delivery      |
| Version:          | v1.0                                                           |
| Milestone Status: | Production Ready                                               |


## **Description:**

This use case describes the implementation of an AI-powered conversational chatbot designed to improve citizen access to digital government services in Kenya. The chatbot, built using PydanticAI agents and Retrieval Augmented Generation (RAG), allows users to interact through text in English and Kiswahili. It guides citizens through various digitized services—such as business registration, film permits, and data protection compliance—by leveraging structured data, document repositories, and knowledge bases from government entities.

The chatbot uses the GovStack Building Block Approach and adheres to principles of open-source development, digital public goods (DPGs), data privacy, and responsible AI. It has been developed for pilot collaboration with Kenya's Directorate of Citizen Services (eCitizen), the Kenya ICT Authority, and the Konza Technopolis. The architecture allows for the onboarding of chatbots from Ministries, Departments, and Agencies (MDAs) within the Kenya government by using a reusable open design.

The solution offers multi-channel access via REST API and web interfaces, and is built for reuse across different sectors and institutions. The chatbot integrates vector databases, document processing pipelines, and comprehensive analytics to provide accurate, relevant, and timely information to citizens while tracking usage and performance metrics.


# ********

# **Stakeholders**

|                                                                               |                                            |
| ----------------------------------------------------------------------------- | ------------------------------------------ |
| **Stakeholder**                                                               | **Role**                                   |
| Citizens (English & Kiswahili speakers)                                       | End users of the chatbot                   |
| Directorate of Citizen Services (eCitizen)                                    | Government implementation partner          |
| ICTA (ICT Authority)                                                          | Government implementation partner          |
| KoTDA (Konza Technopolis Development Authority)                               | Government implementation partner          |
| GIZ FAIR Forward & GiZ Kenya - Digital Transformation Center (DTC) & GovStack | Technical and financial support partner    |
| ITU - International Telecommunications Union                                  | Technical Support                          |
| Tech Innovators Network (THiNK) Ltd                                           | Contractor / Developer                     |
| Local AI/NLP community                                                        | Knowledge transfer and model contributions |
| Government MDAs                                                               | Content providers and service owners       |


# **Sustainable Development Goals (SDGs)**

### **Goal 9.C –** Significantly increase access to information and communications technology and strive to provide universal and affordable access to the Internet.

### **Goal 16.6 –** Develop effective, accountable and transparent institutions at all levels.

### **Goal 17.6 –** Enhance cooperation on and access to science, technology, and innovation.

# ********

# **Building Blocks**

- Information Mediator

- Identity

- Consent

- Messaging

- Workflow

- Registration

- Data Management


# **Source Documents**

GovStack Use Case Specification:

<https://govstack.gitbook.io/specification>

GovStack Use Case Template:

<https://govstack.gitbook.io/use-cases/use-cases-development/use-cases/less-than-use-case-template-greater-than>

Kenya Data Protection Act: 

<https://kenyalaw.org/kl/fileadmin/pdfdownloads/LegalNotices/2021/LN263_2021.pdf>


# **Preconditions / Triggers**

- Citizen must initiate a service-related query through REST API endpoint (/chat/)

- Internet access and valid API key authentication required for platform access


# ********

# **Steps/High-Level Process Flow**

## **1 - User Inquiry Initiation**

A citizen initiates a query to the chatbot through REST API, asking for guidance on accessing a government service (e.g., "How do I register a business?").


### **Workflows:**

- Chat endpoint receives message via POST /chat/ with session management
- User authentication via API key validation system
- Session persistence with PostgreSQL database storage

### **Building Blocks:**

- Messaging (FastAPI REST endpoints)

- Identity (API key authentication)

- Registration (User session management)


## **2 - Intent & Entity Extraction**

The chatbot uses PydanticAI agents to determine the intent (e.g., "business registration") and extract relevant entities from user queries.

**Workflows:**

- PydanticAI agent processes user message with type-safe validation
- RAG pipeline queries ChromaDB vector database for relevant document chunks
- LlamaIndex retrieval system assembles context from multiple government collections

### **Building Blocks:**

- Workflow (PydanticAI orchestration)

- Data Management (ChromaDB vector storage)

- Information Mediator (RAG pipeline integration)


## **3 - Service Discovery and Information Retrieval**

The bot retrieves relevant service information from indexed document collections and web-crawled content via the RAG system.


### **Workflows:**

- ChromaDB semantic search across indexed government documents and webpages
- Content retrieved from collections including KFC, BRS, KFCB, and ODPC knowledge bases
- MinIO object storage provides document access with presigned URLs

### **Building Blocks:**

- Information Mediator (Document and webpage retrieval)

- Workflow (Multi-source content aggregation)

- Consent (Data access permissions via collection management)


## **4 - Response Generation & User Guidance**

Chatbot generates structured responses using OpenAI GPT-4o with source attribution and confidence scoring.


### **Workflows:**

- GPT-4o processes retrieved context to generate comprehensive answers
- Response includes source citations, confidence scores, and recommended follow-up questions
- Message persistence with conversation history maintenance

### **Building Blocks:**

- Messaging (Structured response delivery)

- Consent (Source attribution and transparency)

- Workflow (Response quality assurance)


## **5 - Feedback and Analytics Collection**

The system tracks conversation metrics, token usage, and performance analytics for continuous improvement.


### **Workflows:**

- Real-time event tracking via WebSocket and REST API endpoints
- Analytics module captures user demographics, usage patterns, and business metrics
- Comprehensive audit trail system logs all user actions and system operations

### **Building Blocks:**

- Data Management (Analytics and audit logging)

- Workflow (Performance monitoring and optimization)


# **Diagrams of the Process/Architecture** 

Data-flow diagram <https://drive.google.com/file/d/1A6KNx0DpVAm-van_TzBlm8TKIBXBSWfz/view?usp=sharing>

Technical Architecture document <https://docs.google.com/document/d/15MoFvdgJflQ2xINYxwxMfRt818R_ZXUx7LmcFtW0_hA/edit?usp=sharing>

Infrastructure Diagram <https://drive.google.com/file/d/1wvE3aCvyY31RIAuTEM6ysWGjL8OBxrKq/view?usp=sharing>


# **Example Implementation**

###  **GitHub Repo –** <https://github.com/think-ke/govstack>

### **GovStack Sandbox Prototype -**

Production API: http://localhost:5000
API Documentation: http://localhost:5000/docs
Analytics Dashboard: http://localhost:3001
Admin Interface: http://localhost:3002


# **Contributors**

- Brian Omwenga – Team Lead, Tech Innovators Network (THiNK)

- Nick Mumero - Lead AI Architect, Tech Innovators Network (THiNK)

- Angela Kanyi - DevOps Engineer, Tech Innovators Network (THiNK)

- Paul Ecil - Fullstack Software Engineer, Tech Innovators Network (THiNK)

- Aisha Mohamed Nur – AI/ML Engineer, Tech Innovators Network (THiNK)

-  GIZ DTC & FAIR Forward Teams

-  eCitizen, ICTA, KoTDA – Pilot Partners

- IndabaX NLP Community – Peer Review and Knowledge Exchange

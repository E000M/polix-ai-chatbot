# PoliX – AI-Powered Informative Chatbot for POLIS University

## Overview
PoliX is an intelligent chatbot developed as a diploma thesis project for POLIS University.  
The system is designed to assist prospective students and applicants by providing instant, accurate, and accessible information about the university.

The chatbot uses Artificial Intelligence (AI) and Natural Language Processing (NLP) techniques, implementing a Retrieval-Augmented Generation (RAG) architecture to improve response quality and contextual understanding.

This project aims to simplify the process of obtaining university information by automating responses related to admissions, academic programs, tuition fees, required documentation, contact information, and general university services.



## Project Objectives

- Provide fast and accurate responses to users.
- Reduce repetitive administrative inquiries.
- Improve accessibility to university information.
- Implement an AI-based retrieval system using local language models.
- Create a scalable chatbot system for future institutional use.
- Improve communication between students and university services.





## Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- Flask

### Artificial Intelligence
- Ollama
- FAISS (Vector Database)
- SentenceTransformers
- Retrieval-Augmented Generation (RAG)

### Authentication
- Firebase Authentication (Google Sign-In)

### Deployment & Testing
- Ngrok
- Google Forms (User Evaluation)




## System Architecture

PoliX follows a modular architecture consisting of multiple layers:

### User Interface Layer
Handles user interaction and presents chatbot responses in a simple and user-friendly environment.

### Application Layer
Processes user requests using Flask API endpoints and connects the frontend with backend services.

### Retrieval Layer
Searches for relevant data using semantic similarity through the FAISS vector database.

### Generation Layer
Uses Ollama local language models to generate accurate and context-aware responses.

### Dataset Layer
Stores and manages university information in structured JSON format.


## Main Features

- AI-powered university information assistant
- Semantic search using vector embeddings
- Retrieval-Augmented Generation (RAG)
- Local LLM integration with Ollama
- Google Authentication system
- Admin panel for dataset management
- Chat history storage
- Quick-access predefined question buttons
- User feedback system
- Responsive user interface design



## Dataset Information

The chatbot uses a custom-built dataset that includes important university-related information such as:

- Bachelor study programs
- Tuition fees
- Admission requirements
- Required registration documents
- Application process
- Contact details
- University location
- Official emails
- Academic services

The dataset is maintained in JSON format to allow easy updates and future scalability.



## Testing and Evaluation

The PoliX system was tested with real users through an evaluation process using Google Forms.

The testing process focused on:

- Accuracy of chatbot responses
- System performance and response speed
- User experience and interface usability
- Reliability of information
- Accessibility and ease of use

The results showed positive feedback, especially regarding the chatbot’s speed, simplicity, and usefulness.



## Future Improvements

Future development of PoliX may include:

- Multilingual support
- Voice interaction functionality
- Integration with official university databases
- Expansion of the dataset
- Improved contextual memory
- Mobile application development
- Enhanced personalization for users



## Academic Purpose

This project was developed for academic and research purposes as part of the Bachelor Thesis in Computer Science at POLIS University.



## Author

**Elsa Murati**  
Bachelor in Computer Science  
POLIS University  
Academic Year 2025–2026

Lloyds Banking Group Hackathon 2025: Lunch & Learn - Google Cloud Platform

> **[Image Note: Cover Slide]** The cover slide features an overhead view of a collaborative workspace with multiple laptops, smartphones, notebooks, and coffee, symbolizing a hackathon or workshop environment.

---

Google Cloud Services

> **[Image Note: Service Icons]** Three abstract icons representing core cloud concepts:
> 
> 1. **Compute/Processing:** A square chip-like icon representing computing power.
>     
> 2. **Networking/Location:** A circular compass-like icon.
>     
> 3. **Speed/Transfer:** Two forward-facing arrows representing data movement or acceleration.
>     

---

Compute Products

Compute Engine

- Run large-scale workloads on virtual machines hosted on Google's infrastructure.
    

App Engine

- A platform for building scalable web apps and mobile backends.
    

Kubernetes Engine

- Run Docker containers on Google's infrastructure, powered by Kubernetes.
    

Cloud Run

- Run stateless containers on a fully managed environment or on Anthos.
    

---

## Where Should I Run My Stuff? (Decision Guide)

> **[Image Note: "Where Should I Run My Stuff?" Flowchart]** This is a complex decision tree comparing four main compute options.
> 
> **Theme:** "It Depends..." but "Pro Tip: You can use them together."

1. Compute Engine

- **Best for:** Existing Systems, Virtual Machines.
    
- **Use this when you need:**
    
    - GPUs, TPUs
        
    - Specific kernel & OS, Windows
        
    - Licensing requirements
        
    - Migrating existing systems
        
    - Network protocols beyond HTTP/S
        
    - 1:1 container to VM mapping
        
    - Databases
        
- **Characteristics:** High control, more operations, adaptable to various team structures & tool preferences.
    

2. Kubernetes Engine

- **Best for:** Containerized Applications.
    
- **Use this when you need:**
    
    - Hybrid & multi-cloud deployments
        
    - Strong CI/CD pipelines
        
    - GPUs, TPUs, Specific OS
        
    - Network protocols beyond HTTP/S
        
- **Characteristics:** Team integration (Dev, Ops, Security work together); organization is open to app architecture updates. Pricing includes committed resources.
    

3. Cloud Run

- **Best for:** Serverless & Clusterless Apps & Containers.
    
- **Use this when you need:**
    
    - Fully-managed infrastructure
        
    - Rapid auto-scaling from and to 0
        
    - HTTP/Websockets/gRPC/Events
        
    - No fixed infrastructure footprint
        
- **Characteristics:** Team is mostly dev-focused; owns build tool & deployment decisions. Usage-based pricing.
    

4. Cloud Functions

- **Best for:** Event-Driven Functions.
    
- **Use this when you need:**
    
    - Event-driven cloud automation
        
    - Lightweight data transformation & enrichment
        
    - Connecting to external systems & APIs
        
    - Extend other cloud services with events & code
        
- **Characteristics:** Serverless, less operations. Team is mostly dev-focused. Usage-based pricing.
    

---

Storage Products

> **[Image Note: Storage Icons]** Icons depicting different storage types: objects (buckets), blocks (disks), and file folders.

Cloud Storage

- Store any type of data, any amount of data, and retrieve it as often as you'd like.
    

Persistent Disk

- Block storage service, fully integrated with Compute Engine and GKE.
    

Local SSD

- Ephemeral locally attached block storage for virtual machines and containers.
    

Filestore

- Fully managed service for file migration and storage. Easily mount file shares on Compute Engine VMs.
    

---

Database Products

> **[Image Note: Database Categories]** Icons representing three main database types:
> 
> 1. **Relational:** A three-pronged structure.
>     
> 2. **Key-Value/Document:** A lightning bolt on a chip.
>     
> 3. **In-memory:** Stacked layers.
>     

Relational

- **Cloud SQL:** Managed MySQL, PostgreSQL, and SQL Server.
    
- **Cloud Spanner:** Cloud-native consistent DB with unlimited global scale.
    

Key Value / Document

- **Cloud Bigtable:** Cloud-native NoSQL wide-column store for large scale, low-latency workloads.
    
- **Firestore:** Cloud-native NoSQL to easily develop rich mobile, web, and IoT applications.
    

In-memory

- **Memorystore:** Fully managed Redis and Memcached for sub-millisecond data access.
    
    - _Integrations shown:_ Redis, DataStax, MongoDB Atlas, Neo4j.
        

---

Data Analytics Products

> **[Image Note: Analytics Workflow Pipeline]** A flow showing data moving from ingestion to analysis.

Data ingestion at any scale

- **Cloud Pub/Sub:** Reliable streaming data pipeline.
    
- **Cloud Data Transfer:** Data ingestion.
    
- **BigQuery Data Transfer.**
    

Data warehousing and data lake

- **Cloud Storage:** Storage for data lakes.
    
- **BigQuery:** Data warehousing.
    
- **Cloud Dataproc:** Managed Spark/Hadoop.
    
- **Cloud Dataflow:** Stream and batch processing (Apache Beam).
    
- **Cloud Dataprep:** Data preparation.
    
- **Cloud Data Fusion:** Data integration.
    
- **Cloud Composer:** Workflow orchestration.
    
- **Cloud Data Catalog:** Data discovery/metadata.
    

Advanced analytics

- **AI Platform:** Machine learning capabilities.
    
- **TensorFlow:** ML framework.
    
- **Looker:** Business intelligence and data visualization.
    
- **Google Sheets:** Spreadsheet integration.
    
- **Database Migration.**
    

---

AI/ML Platform

Cloud AI Building Blocks (Pre-Packaged)

- **Sight:** Cloud Vision API, Cloud Video Intelligence API.
    
- **Language:** Cloud Natural Language API, Cloud Translation API.
    
- **Conversation:** Cloud Speech-to-Text API, Cloud Text-to-Speech API, Dialogflow Enterprise.
    

Custom and Automated

- **AutoML Vision**
    
- **AutoML Natural Language**
    
- **AutoML Translation**
    
- **AutoML Speech-to-Text**
    
- **Contact Center AI**
    
- **Cloud Jobs API**
    

Cloud AI Platform (Custom)

- **Tools:** Kubeflow Pipelines, Datasets, AI Hub, Kaggle (Marketplace).
    
- **Services:** Cloud ML Engine, Cloud Dataflow, Cloud Dataproc, Google BigQuery, BigQuery ML, Cloud Dataprep, Google Data Studio.
    
- **Infrastructure:** Cloud TPU, Cloud GPU, Kubeflow.
    
- **ML Libraries:** TensorFlow, PyTorch, Scikit-learn, Apache Beam, Spark MLlib, Keras.
    

---

Platform & Resources

Google Cloud Console Access

1. Navigate to `console.cloud.google.com`
    
2. Select a username and password from the given list.
    
3. Once you login, on top left select the org `green-tartan1.workshop.ongcp.co`
    
4. Select a project `XXXXXXXXX`
    
5. **Rule:** One Project per team.
    

---

Cloud Functions Guide

> **[Image Note: Screenshot of Cloud Functions Documentation]** The image shows the Google Cloud documentation page for Cloud Functions. It highlights the "Quickstarts" section and specifically the "Create and deploy a Cloud Function (1st gen) by using the Google Cloud CLI" tutorial.

- **Resources available:** Overview, Guides, Reference, Samples, Support, Resources.
    
- **Quickstarts:** Cloud Console Quickstart, gcloud Quickstart.
    
- **Steps covered in docs:**
    
    - Get the sample code
        
    - Deploy a function
        
    - Test the function
        
    - Delete the function
        
- _Note:_ There is a distinction between 1st Gen and 2nd Gen functions.
    

---

IDE: Cloud Shell Editor

> **[Image Note: Cloud Shell Editor Interface]** A screenshot of the Cloud Shell Editor (an online IDE based on Theia/VS Code). * **URL:** `ide.cloud.google.com`
> 
> - **Features:** Online development environment available from any browser. Pre-configured with key dependencies and tools.
>     
> - **Code Example (Go):** The editor displays a `main.go` file for a simple "Hello World" web server. It imports `fmt`, `log`, and `net/http`, reads a `PORT` environment variable, and starts a server that prints "Hello, world!" to the response writer. * **Tools visible:** Cloud Code, Minikube, Go Modules support.
>     

---

Where to Find More Info

- **Google Cloud Products in 4 words:** `http://goo.gle/GCP4words`
    
- **Datasets:** `https://www.kaggle.com/datasets`
    
- **Google Cloud Documentation:** `https://cloud.google.com/docs`
    
- **Google Cloud Console:** `https://console.cloud.google.com`
    
- **Quick Architecture tool:** `https://googlecloudcheatsheet.withgoogle.com/log-in?referer=/architecture`
    
- **Codelabs:** `https://codelabs.developers.google.com/`
    
- **Cloud Skillsboost:** `https://www.cloudskillsboost.google/`
    
- **Google Cloud Sketches:** `https://github.com/priyankavergadia/GCPSketchnote`
    
- **Quickstarts:** `https://cloud.google.com/docs/tutorials?doctype=quickstart`
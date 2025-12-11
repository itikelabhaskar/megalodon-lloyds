# NayaOne Hackathon Environment Guide

This document consolidates **all instructions, environment details, setup steps, and workflow guidelines** extracted from the provided PDF (Getting Started Guide). It is designed to be consumed by **another LLM**, so clarity, structure, and completeness have been maximized.

---

# 1. Access the Hackathon Platform

## 1.1 Create Your Account

* You will receive an invite to the platform.
* If this is your first time:

  * Click **“Sign up for an account”** on the login page.
  * Enter your work email and create a password.
  * Complete registration to activate your account.

## 1.2 Access the Hackathon Event

* After signing in, you land on the **Welcome Page**.
* Scroll to **“Check out Events”**.
* Open **“IP&I Hackathon”**.

## 1.3 Explore the Event Tabs

* **Overview:** description, goals, participants.
* **Timeline:** key dates and milestones.
* **Media:** videos and multimedia.
* **Resource:** documents, guides, including this Getting Started Guide.

## 1.4 View the Challenges

* Go to **Challenges** tab.
* Open **“AI Solutions for IP&I on GCP”**.

## 1.5 Projects Tab

* In **Projects**, select your team’s project space.
* Admins/support can see all projects.

## 1.6 Customize Project Description

* Inside the project space, edit the **Description** to include team summary, goals, notes.

## 1.7 Developer Workspaces

Each project includes:

* **5 Developer Workspaces** (one per team member)
* **1 Support Workspace** (LBG + GCP Guardians)

Assign workspaces internally.

---

# 2. Access Developer Workspaces

When you open a developer workspace, you land on the **Credentials tab**.

### 2.1 Workspace Credentials Provided

You are given credentials for:

1. **IDE Login** (VSCode)
2. **OpenAI API key** for Cline Coding Assistant
3. **GCP Access**
4. **GitLab Credentials**

Each credential contains:

* Role
* Username
* Password

### 2.2 Launch the Workspace

* Click **Launch the Workspace**.
* New tab opens.
* Click **Sign in with GitLab**.

### 2.3 Enter IDE Credentials

* Copy IDE username/password from Credentials tab.
* Paste into GitLab sign-in form.

### 2.4 Open the IDE

* After signing in, click the **VS Code icon**.

---

# 3. (Optional) Set Up Coding Assistant (Cline)

### 3.1 Enable the Cline Extension

* Open **Extensions** → search **Cline** → click **Enable (Workspace)**.

### 3.2 Start Cline Setup

* Open Cline panel.
* Choose **Bring my own API key**.

### 3.3 Copy Your API Key

* Go to Developer Workspace → Credentials.
* Copy API key from **Cline - Coding Assistant** row.

### 3.4 Configure Provider

* Provider = **OpenAI**.
* Paste your API key.

### 3.5 Start Using the Assistant

* Begin typing prompts.
* Must repeat setup when workspace restarts.

---

# 4. Access GCP Console

### 4.1 Copy GCP Console URL

* From **3) GCP credential row** copy the URL.

### 4.2 Open Login Page

* Paste URL into new browser tab.

### 4.3 Enter Credentials

* Copy/paste GCP username + password.

### 4.4 Skip Browser Setup

* Select **Continue without setting up browser**.

### 4.5 Access Team GCP Project

* You now access the shared team project.
* Access is restricted to the **NayaOne platform network**.
* Note your **Project ID** – needed for terminal access.

---

# 5. Setup GCP Access in VS Code IDE

### 5.1 Open Terminal

* VSCode → Terminal → **New Terminal**.

### 5.2 Install Google Cloud SDK (gcloud)

Run inside terminal:

```
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates gnupg curl
sudo mkdir -p /usr/share/keyrings
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update
sudo apt-get install -y google-cloud-cli
gcloud --version
```

### 5.3 Generate Auth Link

```
gcloud auth login
```

* Copy login URL.
* Open it **inside Developer Workspace**.

### 5.4 Sign In

* Use the GCP credentials.

### 5.5 Authorise Login

* Approve access.
* Copy verification code.
* Paste into terminal.

### 5.6 Set Project ID

```
gcloud config set project <PROJECT_ID>
```

### 5.7 Check Auth

```
gcloud auth list
```

Should show NayaOne GCP user as active account.

---

# 6. Access GitLab Console & Repo

### 6.1 Copy Repo URL

* From **Repo row** in Credentials tab.

### 6.2 Open GitLab

* Paste URL into Developer Workspace browser.

### 6.3 Explore GitLab

* Use **Explore projects**.

### 6.4 Open Your Repo

* Select your team repo.

### 6.5 Clone Repo in VS Code

* Get HTTPS URL via **Code → Clone with HTTPS**.
* In VSCode terminal:

```
git clone <HTTPS_URL>
```

---

# 7. Data Access

* You can pull data from the shared **GCP Bucket**.
* You **cannot push** to it.
* Ensure terminal is configured to correct project.

---

# 8. QuickStart - Test Setup

A quick validation checklist:

* IDE access works
* Cline extension works
* GitLab repo cloned
* GCP login authenticated
* Project ID set
* gcloud commands functioning

---

# 9. FAQs

General information and troubleshooting (as seen in PDF).

---

# 10. Additional Notes

* Cline setup must be repeated every time workspace restarts (chat history persists).
* All access (IDE, GCP, GitLab) is locked to the NayaOne controlled environment.

---

**End of consolidated NayaOne.md**

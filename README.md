# 🌿 Garden of Secrets: AWS Lambda Secret Manager 🌱  
*An Open-Source Lightweight Secret Manager*  
Created & Maintained by **CatalogFi**  

---

## 🌸 Introduction  

**Garden of Secrets** is a **serverless secret management system** built on **AWS Lambda** and **AWS S3**.  
It provides a beautiful, intuitive, and secure web interface to **store**, **manage**, and **retrieve secrets** — like planting and nurturing secrets in a serene digital garden. 🌼  

💡 **Key Benefits:**  
- 🌲 **Secrets stored securely in AWS S3**  
- 🧑‍🌾 **User & Admin roles** to control access  
- 🔍 **Searchable Secret Explorer** with intuitive UI  
- 🛠️ **Complete CRUD operations** (Create, Read, Update, Delete)  
- 🔒 **Mask/unmask sensitive information**  
- 📜 **Metadata tracking** (ownership & history)  
- 🎉 **Confetti joy** when secrets bloom 🌸  
- 🌐 **Direct Lambda Function URL** – no API Gateway complexity!  

---

## ⚠️ Prerequisites 🌻  

Before planting the seeds of your **Garden of Secrets**, make sure you have:  

- ✅ **AWS Account**  
- ✅ **AWS CLI** configured (`aws configure`)  
- ✅ **AWS Lambda** to serve the application  
- ✅ **AWS S3 Bucket** to store secrets  
- ✅ **IAM Role** with appropriate permissions  

---

## 🌾 Step-by-Step Deployment 🌾  

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/catalogfi/garden-of-secrets.git
cd garden-of-secrets
```

---

### 2️⃣ Create an S3 Bucket (The Soil)  

- Go to **AWS Console → S3 → Create Bucket**  
- Name it something like: **`my-secrets-bucket-123456`**  
- Ensure **public access is blocked**  
- Copy your **Bucket ARN** — it will look like this:  
  ```
  arn:aws:s3:::my-secrets-bucket-123456
  ```

---

### 3️⃣ Create an IAM Policy (The Garden Fence 🌱)  

We need to define who can access our **secret garden**.  

- Go to **AWS Console → IAM → Policies → Create Policy**.  
- Switch to the **JSON** editor and **paste the policy below**:  

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": [
				"s3:ListBucket",
				"s3:GetObject",
				"s3:PutObject",
				"s3:DeleteObject"
			],
			"Resource": [
				"arn:aws:s3:::my-secrets-bucket-123456",
				"arn:aws:s3:::my-secrets-bucket-123456/*"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"logs:CreateLogGroup",
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			"Resource": [
				"arn:aws:logs:*:*:*"
			]
		}
	]
}
```

🌿 **Important:**  
🔁 **Replace:**  
- `my-secrets-bucket-123456` with your **actual S3 bucket ARN**.  
💡 For example:  
```json
"arn:aws:s3:::your-bucket-name"
"arn:aws:s3:::your-bucket-name/*"
```

---

### 4️⃣ Attach Policy to Lambda Execution Role 🌼  

- Go to **AWS Console → IAM → Roles**.  
- Find or create the **Lambda execution role**.  
- Click **Attach Policies** → Search for the **policy you created** → **Attach it**.  

---

### 5️⃣ Update Lambda Code  

🌸 Let's prepare our **Lambda garden**:  

- **Install dependencies**:  
  ```bash
  pip install boto3 -t .
  ```

- **Package code into a ZIP file**:  
  ```bash
  zip -r garden-of-secrets.zip . -x "*.git*" "*__pycache__*"
  ```

- **Deploy to AWS Lambda**:  
  - Open **AWS Console → Lambda → Create Function**.  
  - Choose **"Author from Scratch"**.  
  - Set:  
    - **Function name**: `garden-of-secrets`  
    - **Runtime**: `Python 3.8+`  
    - **Execution Role**: Select the role you just attached the policy to.  
  - **Upload `garden-of-secrets.zip`**.  

### Upload Code to Lambda Function 🌿

- **Upload code to Lambda function**:
  - Open your terminal and ensure AWS CLI is configured. Update the `<your_lambda_function_name>` and `<update-your-region>` placeholders:
  ```bash
  aws lambda update-function-code --function-name <your_lambda_function_name> --zip-file fileb://garden-of-secrets.zip --region <update-your-region>
  ```

- **Set `app.py` as Handler**:
  - Alternatively, you can rename `app.py` to `lambda_function.py`. Update the `<your_lambda_function_name>` and `<update-your-region>` placeholders:
  ```bash
  aws lambda update-function-configuration --function-name <your_lambda_function_name> --handler app.lambda_handler --region <update-your-region>
  ```
---

### 6️⃣ Configure Environment Variables 🌼  

Go to **AWS Lambda → garden-of-secrets → Configuration → Environment Variables**.  

Add:  
| Key            | Value                        |
|----------------|-----------------------------|
| `SECRETS_BUCKET` | `my-secrets-bucket-123456`     |

🌼 **Remember:** Use your **actual bucket name**!  

---

### 7️⃣ Enable Lambda Function URL 🌐  

AWS Lambda **Function URLs** provide an easy, HTTPS-protected endpoint directly linked to your function. No API Gateway required! 🌿  

- Go to **AWS Lambda → garden-of-secrets → Configuration → Function URL**.  
- **Click "Create Function URL"**.  
- Set **Auth type** to **"AWS_IAM"** for restricted access or **"NONE"** if you want anyone with the URL to access (not recommended).  

🔍 **Copy the Function URL** — it should look like this:  

```bash
https://<function-id>.lambda-url.<region>.on.aws/
```

---

## 🌐 Access the Garden 🌸  

Open your **Function URL** in your browser:  

```bash
https://<function-id>.lambda-url.<region>.on.aws/
```

---

## 🛠️ Garden API Paths 🛤️  

| 🛠️ **Method** | 📍 **Endpoint**                  | 🌱 **Action**                |
|-----------------|--------------------------------|-------------------------------|
| **GET**         | `/list`                         | List all accessible secrets    |
| **GET**         | `/get?key=<key>`                | Retrieve secret content        |
| **GET**         | `/meta?key=<key>`               | Get secret metadata            |
| **POST**        | `/create?key=<key>`             | Create a new secret            |
| **POST**        | `/save?key=<key>`               | Update an existing secret      |
| **DELETE**      | `/delete?key=<key>`             | Delete a secret                |
| **POST**        | `/rename?oldKey=<o>&newKey=<n>` | Rename a secret                |
| **GET**         | `/exists?key=<key>`             | Check if secret exists         |

---

## 🌼 Login to the Garden  

🌸 **Garden of Secrets** uses **Basic Authentication**.  

💾 **Default Credentials:**  

| Username | Password | Role  |
|----------|----------|-------|
| `alice`  | password1 | User  |
| `bob`    | password2 | User  |
| `carol`  | 12345     | Admin |

🔍 **Access Rules:**  
- 🌱 **Users:** Can access only **their own secrets**.  
- 🌲 **Admins:** Have access to **all secrets**.  

🌸 **Change these credentials** in the code (in the `USERS` dictionary) as needed.  

---

## 🔒 Security Tips  

🌿 **Harden Your Garden!**  

- 🔑 **Avoid plaintext passwords** — Use AWS Cognito for auth.  
- 🔍 **Audit IAM roles** regularly.  
- 🌐 **Function URLs are already HTTPS-enabled** — use IAM auth if needed.  
- 🛠️ **Encrypt secrets** at rest & in transit.  

---

## 🌸 License  

**MIT License** – Open-source & free to use.  

🌱 **Brought to you by CatalogFi** – because secrets deserve a safe garden to grow.  

---

## 🤝 Community  

🌸 **Contribute to the Garden!**  
- **Fork** the repo  
- **Create** new branches  
- **Submit** pull requests  

Together, let's grow this secret garden into a mighty forest. 🌳💚  

---

Happy Gardening! 🌱🔒🛠️
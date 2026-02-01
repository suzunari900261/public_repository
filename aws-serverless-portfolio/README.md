# AWS CDK Infrastructure

本ディレクトリは、ポートフォリオサイト（サーバーレス Web アプリケーション）の  
**AWS インフラ構成を AWS CDK（Python）で管理するためのコード**です。

CloudFormation テンプレートを直接管理していた構成から、  
**再利用性・保守性・変更容易性の向上**を目的として CDK へ移行しています。

---

## 🎯 目的

- サーバーレス Web アプリケーションのインフラを IaC で管理
- GitHub 起点の CI/CD パイプラインから安全にデプロイ可能な構成とする
- CloudFormation Change Set を用いた **差分確認・手動承認を前提とした運用**を想定

---

## 🏗️ 管理対象リソース

本 CDK スタックでは、以下の AWS リソースを管理しています。

- CloudFront
- S3（静的コンテンツ格納）
- API Gateway
- Lambda（Python）
- SNS（問い合わせ通知）
- Route53
- ACM
- IAM（最小権限）

---

## 🧩 ディレクトリ構成（例）

```text
cdk/
├─ app.py                 # CDK アプリケーションのエントリポイント
├─ stacks/
│  ├─ frontend_stack.py   # CloudFront / S3 / ACM
│  ├─ api_stack.py        # API Gateway / Lambda
│  ├─ dns_stack.py        # Route53
│  └─ notification_stack.py # SNS
├─ constructs/
│  ├─ cloudfront.py
│  ├─ api.py
│  └─ lambda_function.py
├─ tests/
│  └─ test_stacks.py
├─ cdk.json
├─ requirements.txt
└─ README.md

import json
import boto3
import base64
import os
from urllib.parse import parse_qs
from datetime import datetime

# -------------------- CONFIG --------------------
S3_BUCKET = os.environ.get("SECRETS_BUCKET", "my-secrets-bucket-123456")
s3 = boto3.client("s3")

# Hard-coded users and passwords
USERS = {
    "alice": "password1",
    "bob":   "password2",
    "carol": "12345"   # admin example
}

# Admin users have full access to all secrets
ADMINS = {"carol"}

# -------------------- FRONTEND HTML + JS --------------------
HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Garden of Secrets</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&display=swap">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" />
  <!-- Canvas Confetti -->
  <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1/dist/confetti.browser.min.js"></script>
  <link rel="icon" type="image/svg+xml" href="https://docs.garden.finance/img/flower.svg">
  <style>
    /* Colors and Layout */
    :root {
      /* Soft background: mostly white, gently fading to lavender */
      --bg-grad-start: #ffffff;  /* white */
      --bg-grad-end:   #9BC8FF;  /* light bluish-lavender */

      /* Top bar in soft pink */
      --color-topbar:  #FCB9C2;

      /* Primary buttons in baby pink */
      --color-buttons: #FFBBD3;

      /* Explorer or accent panel in pastel blue */
      --color-explorer: #8DCOFF;

      /* Editor or secondary panel in peach */
      --color-editor:  #FDD79D;

      /* (Mint #7BDCBA can be used for small highlights or an alternate panel) */

      /* Keep your existing text & border colors */
      --text-color:    #333;
      --muted-text:    #666;
      --border-color:  #ddd;
      --white:         #fff;
    }



    html, body {
      margin: 0;
      padding: 0;
      height: 100vh;
      width: 100vw;
      font-family: 'Fira Code', monospace;
      color: var(--text-color);

      /* Subtle gradient from white to lavender */
      background: linear-gradient(to right, var(--bg-grad-start) 60%, var(--bg-grad-end) 100%);
      display: flex;
      flex-direction: column;
    }


    /* Top Bar */
    .top-bar {
      background: var(--color-topbar);
      padding: 0.6rem 1rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      border-bottom: 2px solid var(--border-color);
      flex-shrink: 0;
    }
    .brand { display: flex; align-items: center; gap: 0.5rem; }
    .brand-logo { height: 40px; }
    .brand-title { font-size: 1.1rem; font-weight: 600; line-height: 1.2; }
    .tagline { font-size: 0.75rem; color: var(--muted-text); font-style: italic; margin-top: 2px; }
    .search-box { position: relative; margin-left: auto; }
    .search-box input {
      border: 1px solid var(--border-color);
      border-radius: 4px;
      padding: 0.3rem 2rem 0.3rem 0.6rem;
      font-size: 0.85rem;
      outline: none;
    }
    .search-box i {
      position: absolute;
      top: 50%;
      right: 0.6rem;
      transform: translateY(-50%);
      color: #999;
      pointer-events: none;
    }
    .top-buttons button {
      background: var(--color-buttons);
      border: 1px solid var(--border-color);
      border-radius: 4px;
      padding: 0.4rem 0.8rem;
      cursor: pointer;
      font-size: 0.85rem;
      color: var(--text-color);
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
    }
    .top-buttons button:hover { opacity: 0.9; }
    /* Main Layout */
    .main-container { display: flex; flex: 1; overflow: hidden; }
    .explorer {
      width: 260px;
      background: var(--color-explorer);
      display: flex;
      flex-direction: column;
      border-right: 2px solid var(--border-color);
    }
    .explorer-header { font-size: 0.9rem; font-weight: 600; padding: 0.5rem 1rem; border-bottom: 2px solid var(--border-color); }
    .explorer-body { flex: 1; overflow-y: auto; padding: 0.5rem; }
    .secret-item {
      background: var(--white);
      border: 1px solid var(--border-color);
      padding: 0.4rem 0.6rem;
      border-radius: 4px;
      margin-bottom: 0.3rem;
      cursor: pointer;
      transition: background 0.2s;
    }
    .secret-item:hover { background: #f9f9f9; }
    .secret-key { font-weight: 500; margin-bottom: 0.2rem; }
    .secret-meta { font-size: 0.75rem; color: var(--muted-text); }
    .editor { flex: 1; display: flex; flex-direction: column; background: var(--color-editor); }
    .editor-header { border-bottom: 2px solid var(--border-color); padding: 0.5rem 1rem; font-size: 0.9rem; font-weight: 600; display: flex; align-items: center; }
    .file-label { margin-right: auto; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
    .editor-container { flex: 1; display: flex; flex-direction: column; padding: 0.5rem; }
    #editorArea {
      flex: 1;
      width: 100%;
      resize: none;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-family: 'Fira Code', monospace;
      font-size: 0.9rem;
      padding: 0.5rem;
      background: var(--white);
      color: var(--text-color);
      line-height: 1.3;
      white-space: pre-wrap;
      overflow-y: auto;
    }
    .meta-box {
      margin-top: 0.5rem;
      font-size: 0.85rem;
      color: var(--muted-text);
      background: var(--white);
      border: 1px solid var(--border-color);
      border-radius: 4px;
      padding: 0.5rem;
      max-height: 100px;
      overflow-y: auto;
    }
    .meta-box .updates { margin-top: 0.3rem; padding-left: 1rem; }
    .meta-box .updates li { margin-bottom: 0.15rem; }
    .masked { color: transparent !important; text-shadow: 0 0 5px rgba(0,0,0,0.5); }
    /* Modal Overlays */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0,0,0,0.5);
      display: none;
      justify-content: center;
      align-items: center;
      z-index: 9999;
    }
    .modal-overlay.active { display: flex; }
    /* Updated Create Secret Modal Styling */
    #createModal .modal {
      width: 90%;
      max-width: 800px;
      padding: 2.5rem;
      background: var(--white);
      border: none;
      border-radius: 8px;
      box-shadow: 0 6px 25px rgba(0,0,0,0.2);
    }
    #createModal h3 {
      font-size: 2rem;
      margin-bottom: 1.5rem;
      color: var(--color-buttons);
    }
    #createModal label {
      display: block;
      margin-bottom: 0.5rem;
      font-size: 1.1rem;
      font-weight: 500;
    }
    #createModal input[type="text"],
    #createModal textarea {
      width: 100%;
      padding: 1rem;
      font-size: 1.1rem;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      box-sizing: border-box;
      margin-bottom: 1.5rem;
    }
    #createModal textarea {
      min-height: 250px;
      resize: vertical;
    }
    #createModal .modal-footer button {
      font-size: 1.1rem;
      padding: 0.75rem 1.5rem;
    }
    /* Default Modal Styling for other modals */
    .modal {
      background: var(--white);
      border: 2px solid var(--border-color);
      border-radius: 4px;
      padding: 1rem;
      width: 480px;
      max-width: 95%;
      color: var(--text-color);
      animation: fadeUp 0.3s ease forwards;
    }
    @keyframes fadeUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    .modal h3 { margin: 0; font-size: 1rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.3rem; color: var(--color-buttons); }
    .modal-footer { margin-top: 1rem; text-align: right; }
    .modal-footer button { margin-left: 0.5rem; background: var(--color-buttons); border: 1px solid var(--border-color); border-radius: 4px; padding: 0.4rem 0.8rem; cursor: pointer; font-size: 0.8rem; }
    .modal-footer button:hover { opacity: 0.9; }
    /* Login Modal */
    #loginModal input {
      width: 100%;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      padding: 0.4rem;
      font-size: 1rem;
    }
    /* Toast */
    #toastContainer {
      position: fixed;
      bottom: 20px;
      right: 20px;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      z-index: 999999;
    }
    .toast {
      display: flex;
      align-items: center;
      padding: 0.75rem 1rem;
      border-radius: 4px;
      border: 2px solid var(--border-color);
      background: var(--white);
      font-size: 0.85rem;
      animation: fadeToast 0.3s ease-out forwards;
      box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    }
    .toast-success { border-color: #99d39f; background: #e8f8ea; }
    .toast-error { border-color: #f8a1a1; background: #fdeaea; }
    @keyframes fadeToast { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
  </style>
</head>
<body>
  <!-- Top Bar -->
  <div class="top-bar">
    <div class="brand">
      <img class="brand-logo" src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjI0MCIgdmlld0JveD0iMCAwIDgwMCAyNDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik03MzMuOTA5IDE2MS40NTlINzE4LjY2MlY4Mi4xNDE4SDczMi40NDlMNzM0LjA3MSA5NC4zMDY5QzczOS4xIDg1LjIyMzYgNzQ5LjE1NiA3OS44NzEgNzYwLjM0OCA3OS44NzFDNzgxLjI3MiA3OS44NzEgNzkwLjg0MiA5Mi42ODQ5IDc5MC44NDIgMTEyLjk2VjE2MS40NTlINzc1LjU5NVYxMTYuMzY2Qzc3NS41OTUgMTAwLjMwOCA3NjguMTM0IDkzLjgyMDMgNzU2LjQ1NSA5My44MjAzQzc0Mi4xODEgOTMuODIwMyA3MzMuOTA5IDEwNC4wMzkgNzMzLjkwOSAxMTkuNDQ4VjE2MS40NTlaIiBmaWxsPSIjNTU0QjZBIi8+CjxwYXRoIGQ9Ik02NjkuMDMgMTYzLjQwNUM2NDUuNjczIDE2My40MDUgNjI5LjYxNSAxNDYuNTM2IDYyOS42MTUgMTIxLjg4MUM2MjkuNjE1IDk3LjA2NDQgNjQ1LjM0OCA3OS44NzEgNjY4LjM4MSA3OS44NzFDNjkwLjkyNyA3OS44NzEgNzA1LjY4NyA5NS40NDI0IDcwNS42ODcgMTE4Ljk2MlYxMjQuNjM5TDY0NC4zNzUgMTI0LjgwMUM2NDUuNTEgMTQxLjUwOCA2NTQuMjY5IDE1MC43NTMgNjY5LjM1NCAxNTAuNzUzQzY4MS4xOTUgMTUwLjc1MyA2ODguOTgxIDE0NS44ODcgNjkxLjU3NiAxMzYuODA0SDcwNS44NUM3MDEuOTU3IDE1My44MzUgNjg4LjY1NiAxNjMuNDA1IDY2OS4wMyAxNjMuNDA1Wk02NjguMzgxIDkyLjY4NDlDNjU1LjA4IDkyLjY4NDkgNjQ2LjY0NiAxMDAuNjMzIDY0NC42OTkgMTE0LjU4Mkg2OTAuNDRDNjkwLjQ0IDEwMS40NDQgNjgxLjg0NCA5Mi42ODQ5IDY2OC4zODEgOTIuNjg0OVoiIGZpbGw9IiM1NTRCNkEiLz4KPHBhdGggZD0iTTU3My4zOTQgMTYzLjQwNUM1NTAuMzYxIDE2My40MDUgNTM2LjQxMiAxNDYuMjEyIDUzNi40MTIgMTIyLjA0M0M1MzYuNDEyIDk3LjcxMzIgNTUwLjUyMyA3OS44NzEgNTc0LjA0MyA3OS44NzFDNTg2LjIwOCA3OS44NzEgNTk2LjQyNyA4NS4yMjM2IDYwMS43NzkgOTQuOTU1OFY0Mi4wNzc5SDYxNi44NjRWMTYxLjQ1OUg2MDMuMjM5TDYwMS45NDEgMTQ3LjAyM0M1OTYuNzUxIDE1Ny44OSA1ODYuMDQ2IDE2My40MDUgNTczLjM5NCAxNjMuNDA1Wk01NzYuNDc2IDE0OS42MThDNTkyLjA0NyAxNDkuNjE4IDYwMS42MTcgMTM4LjEwMSA2MDEuNjE3IDEyMS41NTdDNjAxLjYxNyAxMDUuMzM3IDU5Mi4wNDcgOTMuNjU4MSA1NzYuNDc2IDkzLjY1ODFDNTYwLjkwNCA5My42NTgxIDU1MS44MjEgMTA1LjMzNyA1NTEuODIxIDEyMS41NTdDNTUxLjgyMSAxMzcuOTM5IDU2MC45MDQgMTQ5LjYxOCA1NzYuNDc2IDE0OS42MThaIiBmaWxsPSIjNTU0QjZBIi8+CjxwYXRoIGQ9Ik01MzQuMjA4IDgxLjQ5M1Y5NS40NDI0SDUyNy4zOTZDNTEyLjk2IDk1LjQ0MjQgNTA0LjAzOSAxMDQuMjAxIDUwNC4wMzkgMTE5LjQ0OFYxNjEuNDU5SDQ4OC43OTJWODIuMzA0SDUwMy4wNjVMNTA0LjAzOSA5NC4zMDdDNTA3LjI4MyA4Ni4wMzQ3IDUxNS4yMzEgODAuNTE5OCA1MjYuMDk4IDgwLjUxOThDNTI4Ljg1NiA4MC41MTk4IDUzMS4xMjYgODAuODQ0MiA1MzQuMjA4IDgxLjQ5M1oiIGZpbGw9IiM1NTRCNkEiLz4KPHBhdGggZD0iTTQyOS4zOTcgMTYzLjQwNUM0MTIuMzY1IDE2My40MDUgNDAyLjMwOSAxNTMuODM1IDQwMi4zMDkgMTM5LjM5OUM0MDIuMzA5IDEyNC44MDEgNDEzLjE3NiAxMTUuNzE4IDQzMS44MyAxMTQuMjU4TDQ1Ni44MDkgMTEyLjMxMVYxMTAuMDQxQzQ1Ni44MDkgOTYuNzQgNDQ4Ljg2MSA5Mi4wMzYxIDQzOC4xNTYgOTIuMDM2MUM0MjUuMzQyIDkyLjAzNjEgNDE4LjA0MyA5Ny43MTMyIDQxOC4wNDMgMTA3LjI4M0g0MDQuNzQyQzQwNC43NDIgOTAuNzM4NSA0MTguMzY3IDc5Ljg3MSA0MzguODA0IDc5Ljg3MUM0NTguNDMxIDc5Ljg3MSA0NzEuNzMxIDkwLjI1MTkgNDcxLjczMSAxMTEuNjYzVjE2MS40NTlINDU4Ljc1NUw0NTcuMTMzIDE0OC42NDVDNDUzLjA3OCAxNTcuNzI4IDQ0Mi4yMTEgMTYzLjQwNSA0MjkuMzk3IDE2My40MDVaTTQzMy43NzYgMTUxLjU2NEM0NDguMjEyIDE1MS41NjQgNDU2Ljk3MSAxNDIuMTU2IDQ1Ni45NzEgMTI3LjIzNFYxMjMuMDE3TDQzNi42OTYgMTI0LjYzOUM0MjMuMjMzIDEyNS45MzYgNDE3LjcxOCAxMzEuMTI3IDQxNy43MTggMTM4LjkxMkM0MTcuNzE4IDE0Ny4zNDcgNDIzLjg4MiAxNTEuNTY0IDQzMy43NzYgMTUxLjU2NFoiIGZpbGw9IiM1NTRCNkEiLz4KPHBhdGggZD0iTTMwOC4yODggMTE5Ljc3M0MzMDguMjg4IDk3LjM4ODggMzIyLjcyNCA3OS44NzEgMzQ1Ljc1NiA3OS44NzFDMzU4LjU3IDc5Ljg3MSAzNjguNDY0IDg1LjcxMDIgMzczLjQ5MyA5NS42MDQ2TDM3NC42MjggODIuMTQxOEgzODguMjUzVjE1OC4yMTRDMzg4LjI1MyAxODMuMTk0IDM3Mi44NDQgMTk5LjA4OSAzNDguNTE0IDE5OS4wODlDMzI2Ljk0MSAxOTkuMDg5IDMxMi4xOCAxODYuOTI0IDMwOS4yNjEgMTY2LjgxMUgzMjQuNTA4QzMyNi40NTQgMTc4LjQ5IDMzNS4yMTMgMTg1LjMwMiAzNDguNTE0IDE4NS4zMDJDMzYzLjQzNiAxODUuMzAyIDM3My4xNjggMTc1LjU3IDM3My4xNjggMTYwLjQ4NVYxNDQuNTlDMzY3Ljk3OCAxNTMuODM1IDM1Ny41OTcgMTU5LjM1IDM0NS4xMDcgMTU5LjM1QzMyMi41NjEgMTU5LjM1IDMwOC4yODggMTQxLjk5NCAzMDguMjg4IDExOS43NzNaTTMyMy41MzUgMTE5LjQ0OEMzMjMuNTM1IDEzNC4zNzEgMzMyLjc4IDE0Ni4wNDkgMzQ3LjcwMyAxNDYuMDQ5QzM2My4xMTIgMTQ2LjA0OSAzNzIuNTIgMTM1LjAyIDM3Mi41MiAxMTkuNDQ4QzM3Mi41MiAxMDQuMjAxIDM2My40MzYgOTMuMTcxNSAzNDcuODY1IDkzLjE3MTVDMzMyLjYxOCA5My4xNzE1IDMyMy41MzUgMTA0Ljg1IDMyMy41MzUgMTE5LjQ0OFoiIGZpbGw9IiM1NTRCNkEiLz4KPHBhdGggZmlsbC1ydWxlPSJldmVub2RkIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0xMTguODE4IDEwQzE0OC40NTEgMTAgMTczLjQ3MSAyOS43ODUyIDE4MS40MjkgNTYuODg2N0MyMDguODc2IDY0LjYwODQgMjI5IDg5Ljg2MDIgMjI5IDExOS44MkMyMjkgMTQ5LjY2NiAyMDkuMDI4IDE3NC44NCAxODEuNzQgMTgyLjY2NUMxNzMuOTI4IDIwOS45OTYgMTQ4Ljc5NiAyMzAgMTE5IDIzMEM4OS4yMDMzIDIzMCA2NC4wNzE0IDIwOS45OTYgNTYuMjU5MSAxODIuNjY1QzI4Ljk3MTcgMTc0Ljg0IDkgMTQ5LjY2NiA5IDExOS44MkM5IDkwLjAwNDcgMjguOTMwNCA2NC44NTIgNTYuMTc0NSA1Ni45OTk2QzY0LjA5NiAyOS44NDAxIDg5LjE0NCAxMCAxMTguODE4IDEwWiIgZmlsbD0iI0Y3Q0ZEQiIvPgo8cGF0aCBkPSJNMTM3Ljk4MSAxMDAuMDAzQzEzNy44MjcgMTEyLjU5NyAxMTguMDUxIDExMC44OSAxMTEuNzU0IDExMC44MTNMMTEyLjAyNiA4OC41Mjc3QzExOC4zMjQgODguNjA0OCAxMzguMTM5IDg2Ljg1MzggMTM3Ljk4MSAxMDAuMDAzWk0xNDIuNzM4IDEzNC43MjJDMTQyLjU3OCAxNDguNTczIDExOC44ODEgMTQ2LjcwMyAxMTEuMzA3IDE0Ni42MTRMMTExLjY5IDEyMi4wNjdDMTE5LjI0IDEyMi4xNyAxNDIuOTk1IDEyMC4yNzggMTQyLjgxNSAxMzQuNzQzTDE0Mi43MzggMTM0LjcyMlpNMTU4LjkxOSA5NS4yOTE2QzE1Ny44MjEgODIuMDUzMiAxNDYuNDY2IDc3LjUwMzcgMTMyLjA3NSA3Ni4wNDIzTDEzMi4zMDEgNTcuNzA4NkwxMjEuMTI4IDU3LjU2MzlMMTIwLjkwNiA3NS40MjM2QzExNy45ODUgNzUuMzg0MSAxMTQuOTg1IDc1LjQwNjEgMTEyLjAwNCA3NS40MzMzTDExMi4xMjcgNTcuNDg0OEwxMDAuOTg0IDU3LjMwNjhMMTAwLjc2NCA3NS42MjEyQzk4LjMzOTUgNzUuNjUyOSA5NS45NjQyIDc1LjY1NjUgOTMuNjU3IDc1LjYzNjlMNzguMjY3MyA3NS40MzU3TDc4LjEyNDggODcuMzcxM0M3OC4xMjQ4IDg3LjM3MTMgODYuMzk4IDg3LjMxNzIgODYuMjExNSA4Ny40NzM3Qzg5LjMzNDUgODcuMTE1OSA5Mi4xNjgzIDg5LjMyNjQgOTIuNTgxNCA5Mi40NDIzTDkyLjM5MTMgMTEzLjI2M0M5Mi43ODQxIDExMy4yNjcgOTMuMTc2MiAxMTMuMjk2IDkzLjU2NTMgMTEzLjM1TDkyLjM4OTkgMTEzLjM0NUw5MS45NjY0IDE0Mi41ODhDOTEuNzgzMSAxNDQuNzcyIDg5Ljg3MjEgMTQ2LjM5OCA4Ny42ODY5IDE0Ni4yMzFDODcuODYwMiAxNDYuMjc3IDc5LjU4MDkgMTQ2LjEyMyA3OS41ODA5IDE0Ni4xMjNMNzcuMTk1MiAxNTkuNDE5TDkxLjcyNDIgMTU5LjU5Nkw5OS43MTQ2IDE1OS42NzNMOTkuNTAwMiAxNzguMTk1TDExMC42NTMgMTc4LjMzNUwxMTAuODE1IDE2MC4wODdDMTEzLjc3OCAxNjAuMiAxMTYuNzU3IDE2MC4yNTUgMTE5LjcyMiAxNjAuMjg1TDExOS40OTMgMTc4LjU1NkwxMzAuNjQ2IDE3OC42OTZMMTMwLjg5OSAxNjAuMTgzQzE0OS43MDcgMTU5LjMzOSAxNjIuODY0IDE1NC43NzIgMTY0LjcwOCAxMzcuMTgyQzE2Ni4xNzUgMTIzIDE1OS42MyAxMTYuNjAxIDE0OS4wMzggMTEzLjkwOEMxNTUuNTU1IDExMC42OTkgMTU5LjY5NSAxMDQuOTU1IDE1OC44NDIgOTUuMjcwOUwxNTguOTE5IDk1LjI5MTZaIiBmaWxsPSIjREI2QTkzIi8+Cjwvc3ZnPgo=" alt="Garden Logo"/>
      <div class="brand-title">
        Garden of Secrets
        <div class="tagline">Sow a secret, watch your garden grow.</div>
      </div>
    </div>
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="Search secrets...">
      <i class="fas fa-search"></i>
    </div>
    <div class="top-buttons">
      <button id="btnNewSecret"><i class="fas fa-plus"></i> New</button>
      <button id="renameBtn"><i class="fas fa-edit"></i> Rename</button>
      <button id="deleteBtn"><i class="fas fa-trash"></i> Delete</button>
      <button id="copyArnBtn"><i class="fas fa-copy"></i> Copy ARN</button>
      <button id="maskBtn"><i class="fas fa-eye-slash"></i> Mask</button>
      <button id="saveBtn"><i class="fas fa-save"></i> Save</button>
    </div>
  </div>
  <!-- Main Layout -->
  <div class="main-container">
    <div class="explorer">
      <div class="explorer-header">SECRETS</div>
      <div class="explorer-body" id="explorerBody"></div>
    </div>
    <div class="editor">
      <div class="editor-header">
        <span class="file-label" id="fileLabel">No secret selected</span>
      </div>
      <div class="editor-container">
        <textarea id="editorArea" placeholder="No secret content..."></textarea>
        <div class="meta-box" id="metaBox" style="display:none;">
          <div id="metaOwner"></div>
          <ul class="updates" id="metaUpdates"></ul>
        </div>
      </div>
    </div>
  </div>
  <div id="toastContainer"></div>

  <!-- Create Secret Modal (Updated Styling) -->
  <div class="modal-overlay" id="createModal">
    <div class="modal">
      <h3><i class="fas fa-plus-circle"></i> Create Secret</h3>
      <label>Secret Key</label>
      <input type="text" id="createKey" placeholder="Enter a unique key">
      <label>Secret Content</label>
      <textarea id="createContent" placeholder="Enter your secret content here..."></textarea>
      <div class="modal-footer">
        <button onclick="hideModal('createModal')">Cancel</button>
        <button onclick="createSecret()">Create</button>
      </div>
    </div>
  </div>

  <!-- Rename Secret Modal -->
  <div class="modal-overlay" id="renameModal">
    <div class="modal">
      <h3><i class="fas fa-edit"></i> Rename Secret</h3>
      <p style="font-size:0.85rem; margin-bottom:0.5rem; color: var(--muted-text);">
        We'll move the content & metadata into the new key, then remove the old key.
      </p>
      <label>Old Key</label>
      <input type="text" id="oldKey" readonly style="width:100%; padding:0.4rem;">
      <label>New Key</label>
      <input type="text" id="newKey" style="width:100%; padding:0.4rem;">
      <div class="modal-footer">
        <button onclick="hideModal('renameModal')">Cancel</button>
        <button onclick="renameSecret()">Rename</button>
      </div>
    </div>
  </div>

  <!-- Login Modal -->
  <div class="modal-overlay" id="loginModal">
    <div class="modal">
      <h3><i class="fas fa-user"></i> Login</h3>
      <label>Username</label>
      <input type="text" id="loginUser">
      <label>Password</label>
      <input type="password" id="loginPass">
      <div class="modal-footer">
        <button onclick="attemptLogin()">Login</button>
      </div>
    </div>
  </div>

  <script>
    let secretsCache = [];
    let currentKey = null;
    let isMasked = false;
    let authHeader = "";

    document.addEventListener("DOMContentLoaded", () => {
      showModal("loginModal");

      document.getElementById("btnNewSecret").addEventListener("click", () => showModal("createModal"));
      document.getElementById("renameBtn").addEventListener("click", openRenameModal);
      document.getElementById("deleteBtn").addEventListener("click", deleteSecret);
      document.getElementById("copyArnBtn").addEventListener("click", copyArn);
      document.getElementById("maskBtn").addEventListener("click", toggleMaskMode);
      document.getElementById("saveBtn").addEventListener("click", saveSecret);
      document.getElementById("searchInput").addEventListener("input", e => renderSecrets(e.target.value));
    });

    async function attemptLogin() {
      const user = document.getElementById("loginUser").value.trim();
      const pass = document.getElementById("loginPass").value;
      if(!user || !pass) {
        showToast("Username & password required.", "error");
        return;
      }
      const token = btoa(`${user}:${pass}`);
      authHeader = "Basic " + token;
      try {
        const res = await fetch("/list", { headers: { "Authorization": authHeader } });
        if(!res.ok) throw new Error("Invalid credentials");
        secretsCache = await res.json();
        hideModal("loginModal");
        showToast("Login successful!", "success");
        renderSecrets();
      } catch(err) {
        showToast("Login failed: " + err.message, "error");
      }
    }

    function showModal(id) { document.getElementById(id).classList.add("active"); }
    function hideModal(id) { document.getElementById(id).classList.remove("active"); }
    function showToast(msg, type="success") {
      const container = document.getElementById("toastContainer");
      const toast = document.createElement("div");
      toast.className = "toast " + (type==="error"?"toast-error":"toast-success");
      toast.textContent = msg;
      container.appendChild(toast);
      setTimeout(() => { toast.style.opacity = "0"; setTimeout(() => container.removeChild(toast),300); }, 3000);
    }
    async function renderSecrets(query="") {
      const explorer = document.getElementById("explorerBody");
      explorer.innerHTML = "";
      let filtered = secretsCache.filter(s => s.Key.toLowerCase().includes(query.toLowerCase()));
      if(filtered.length===0){
        explorer.innerHTML = "<p style='color: var(--muted-text);'>No secrets found</p>";
        return;
      }
      filtered.forEach(obj => {
        const date = new Date(obj.LastModified).toLocaleDateString();
        const div = document.createElement("div");
        div.className = "secret-item";
        div.innerHTML = `<div class="secret-key">${obj.Key}</div>
                         <div class="secret-meta">${date} | ${obj.Size} bytes</div>`;
        div.addEventListener("click", () => openSecret(obj.Key));
        explorer.appendChild(div);
      });
    }
    async function refreshList() {
      const r = await fetch("/list", { headers: { "Authorization": authHeader } });
      secretsCache = await r.json();
      renderSecrets();
    }
    async function openSecret(key) {
      try {
        const [contentRes, metaRes] = await Promise.all([
          fetch("/get?key=" + encodeURIComponent(key), { headers: { "Authorization": authHeader } }),
          fetch("/meta?key=" + encodeURIComponent(key), { headers: { "Authorization": authHeader } })
        ]);
        if(!contentRes.ok) throw new Error(await contentRes.text());
        if(!metaRes.ok) throw new Error(await metaRes.text());
        const content = await contentRes.text();
        const meta = await metaRes.json();
        currentKey = key;
        document.getElementById("fileLabel").textContent = key;
        document.getElementById("editorArea").value = content;
        isMasked = false;
        updateMaskUI();
        document.getElementById("metaBox").style.display = "block";
        document.getElementById("metaOwner").textContent = "Owner: " + meta.Owner;
        const updatesUl = document.getElementById("metaUpdates");
        updatesUl.innerHTML = "";
        (meta.Updates||[]).forEach(u => {
          const li = document.createElement("li");
          li.textContent = `${u.time} | ${u.user} | ${u.action}`;
          updatesUl.appendChild(li);
        });
      } catch(err) {
        showToast("Error opening secret: " + err.message, "error");
      }
    }
    async function createSecret() {
      const key = document.getElementById("createKey").value.trim();
      const content = document.getElementById("createContent").value;
      if(!key) { showToast("Key is required", "error"); return; }
      try {
        const res = await fetch("/create?key="+encodeURIComponent(key), {
          method: "POST",
          headers: { "Authorization": authHeader },
          body: content
        });
        if(res.status===409) { showToast("Key already exists", "error"); return; }
        if(!res.ok) throw new Error(await res.text());
        showToast("Secret created!", "success");
        hideModal("createModal");
        document.getElementById("createKey").value = "";
        document.getElementById("createContent").value = "";
        await refreshList();
        confettiMagic();
      } catch(err) {
        showToast("Create failed: "+err.message, "error");
      }
    }
    async function saveSecret() {
      if(!currentKey) { showToast("No secret open to save", "error"); return; }
      const body = document.getElementById("editorArea").value;
      try {
        const res = await fetch("/save?key="+encodeURIComponent(currentKey), {
          method: "POST",
          headers: { "Authorization": authHeader },
          body
        });
        if(!res.ok) throw new Error(await res.text());
        showToast("Secret updated!", "success");
        await refreshList();
        openSecret(currentKey);
        confettiMagic();
      } catch(err) {
        showToast("Save failed: " + err.message, "error");
      }
    }
    async function deleteSecret() {
      if(!currentKey) { showToast("No secret open to delete", "error"); return; }
      if(!confirm("Are you sure you want to delete '" + currentKey + "'?")) return;
      try {
        const res = await fetch("/delete?key="+encodeURIComponent(currentKey), {
          method: "DELETE",
          headers: { "Authorization": authHeader }
        });
        if(!res.ok) throw new Error(await res.text());
        showToast("Secret deleted!", "success");
        currentKey = null;
        document.getElementById("fileLabel").textContent = "No secret selected";
        document.getElementById("editorArea").value = "";
        document.getElementById("metaBox").style.display = "none";
        await refreshList();
        confettiMagic();
      } catch(err) {
        showToast("Delete failed: " + err.message, "error");
      }
    }
    function openRenameModal(){
      if(!currentKey) { showToast("No secret open for rename", "error"); return; }
      document.getElementById("oldKey").value = currentKey;
      document.getElementById("newKey").value = "";
      showModal("renameModal");
    }
    async function renameSecret() {
      const oldK = document.getElementById("oldKey").value.trim();
      const newK = document.getElementById("newKey").value.trim();
      if(!newK) { showToast("New key is required", "error"); return; }
      if(oldK===newK) { showToast("New key same as old key", "error"); return; }
      try {
        const check = await fetch("/exists?key="+encodeURIComponent(newK), { headers: { "Authorization": authHeader } });
        if(check.ok) { showToast("New key already exists", "error"); return; }
        const renameReq = await fetch(`/rename?oldKey=${encodeURIComponent(oldK)}&newKey=${encodeURIComponent(newK)}`, {
          method: "POST",
          headers: { "Authorization": authHeader }
        });
        if(!renameReq.ok) throw new Error(await renameReq.text());
        showToast(`Renamed ${oldK} -> ${newK}`, "success");
        hideModal("renameModal");
        await refreshList();
        openSecret(newK);
        confettiMagic();
      } catch(err) {
        showToast("Rename failed: "+err.message, "error");
      }
    }
    function toggleMaskMode() {
      isMasked = !isMasked;
      updateMaskUI();
    }
    function updateMaskUI() {
      const btn = document.getElementById("maskBtn");
      const area = document.getElementById("editorArea");
      if(isMasked) {
        btn.innerHTML = `<i class="fas fa-eye"></i> Unmask`;
        area.classList.add("masked");
      } else {
        btn.innerHTML = `<i class="fas fa-eye-slash"></i> Mask`;
        area.classList.remove("masked");
      }
    }
    function copyArn() {
      if(!currentKey){
        showToast("No secret open to copy ARN", "error");
        return;
      }
      const arn = "arn:aws:s3:::" + "REPLACE_WITH_YOUR_BUCKET" + "/" + currentKey;
      navigator.clipboard.writeText(arn)
        .then(()=>showToast("ARN copied: "+arn,"success"))
        .catch(()=>showToast("Copy failed","error"));
    }
    function confettiMagic() {
      const duration = 2000;
      const end = Date.now() + duration;
      (function frame(){
        confetti({ particleCount:4, angle:60, spread:55, origin:{x:0} });
        confetti({ particleCount:4, angle:120, spread:55, origin:{x:1} });
        if(Date.now()<end) requestAnimationFrame(frame);
      })();
    }
  </script>
</body>
</html>
"""

# Replace placeholder bucket name with the actual bucket name from the environment.
HTML_PAGE = HTML_PAGE.replace("REPLACE_WITH_YOUR_BUCKET", S3_BUCKET)

# -------------------- PYTHON BACKEND --------------------
def check_auth(event):
    headers = event.get("headers") or {}
    auth_header = headers.get("authorization") or headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return False, None
    try:
        encoded = auth_header.split(" ", 1)[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
        if USERS.get(username) == password:
            return True, username
    except Exception:
        pass
    return False, None

def is_admin(user: str) -> bool:
    return user in ADMINS

def get_metadata(key):
    try:
        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
        meta = head.get("Metadata", {})
        owner = meta.get("owner", "")
        updates_str = meta.get("updates", "[]")
        updates = json.loads(updates_str)
        return owner, updates
    except s3.exceptions.NoSuchKey:
        return None, None
    except Exception:
        return None, None

def user_can_access(key, user):
    if is_admin(user):
        return True
    owner, _ = get_metadata(key)
    if owner is None:
        return False
    return owner == user

def put_object_with_metadata(key, content, owner, updates):
    updates_str = json.dumps(updates)
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=content,
        ServerSideEncryption="AES256",
        Metadata={
            "owner": owner,
            "updates": updates_str
        }
    )

def lambda_handler(event, context):
    path = event.get("rawPath", "/")
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if path == "/" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": HTML_PAGE
        }
    authorized, current_user = check_auth(event)
    if not authorized:
        return {
            "statusCode": 401,
            "headers": {"WWW-Authenticate": 'Basic realm="GardenOfSecrets"'},
            "body": "Unauthorized"
        }
    params = parse_qs(event.get("rawQueryString", ""))
    if path == "/list" and method == "GET":
        try:
            resp = s3.list_objects_v2(Bucket=S3_BUCKET)
            contents = resp.get("Contents", [])
            secrets_info = []
            for obj in contents:
                key = obj["Key"]
                owner, _ = get_metadata(key)
                if owner is None:
                    continue
                if is_admin(current_user) or (owner == current_user):
                    secrets_info.append({
                        "Key": key,
                        "LastModified": obj["LastModified"].isoformat(),
                        "Size": obj["Size"]
                    })
            return {"statusCode": 200, "body": json.dumps(secrets_info)}
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    elif path == "/get" and method == "GET":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
            content = obj["Body"].read().decode("utf-8")
            return {"statusCode": 200, "body": content}
        except s3.exceptions.NoSuchKey:
            return {"statusCode": 404, "body": "Not found"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
    elif path == "/meta" and method == "GET":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        owner, updates = get_metadata(key)
        if owner is None:
            return {"statusCode": 404, "body": "Not found"}
        return {"statusCode": 200, "body": json.dumps({"Owner": owner, "Updates": updates})}
    elif path == "/create" and method == "POST":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=key)
            return {"statusCode": 409, "body": "Secret key already exists"}
        except s3.exceptions.ClientError:
            pass
        content = event.get("body", "") or ""
        updates = [{
            "user": current_user,
            "time": datetime.utcnow().isoformat() + "Z",
            "action": "create"
        }]
        try:
            put_object_with_metadata(key, content, current_user, updates)
            return {"statusCode": 201, "body": "Created"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
    elif path == "/save" and method == "POST":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        content = event.get("body", "") or ""
        try:
            head = s3.head_object(Bucket=S3_BUCKET, Key=key)
            meta = head.get("Metadata", {})
            owner = meta.get("owner", current_user)
            updates = json.loads(meta.get("updates", "[]"))
        except s3.exceptions.NoSuchKey:
            return {"statusCode": 404, "body": "No existing secret to update"}
        updates.append({
            "user": current_user,
            "time": datetime.utcnow().isoformat() + "Z",
            "action": "update"
        })
        try:
            put_object_with_metadata(key, content, owner, updates)
            return {"statusCode": 200, "body": "Updated"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
    elif path == "/delete" and method == "DELETE":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=key)
            return {"statusCode": 200, "body": "Deleted"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
    elif path == "/exists" and method == "GET":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=key)
        except s3.exceptions.ClientError:
            return {"statusCode": 404, "body": "Key not found"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        return {"statusCode": 200, "body": "Key exists"}
    elif path == "/rename" and method == "POST":
        old_key = params.get("oldKey", [""])[0]
        new_key = params.get("newKey", [""])[0]
        if not old_key or not new_key:
            return {"statusCode": 400, "body": "Missing 'oldKey' or 'newKey' param"}
        if not user_can_access(old_key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=old_key)
            old_content = obj["Body"].read()
            head = s3.head_object(Bucket=S3_BUCKET, Key=old_key)
            meta = head.get("Metadata", {})
            owner = meta.get("owner", current_user)
            updates = json.loads(meta.get("updates", "[]"))
        except s3.exceptions.NoSuchKey:
            return {"statusCode": 404, "body": "Old key not found"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=new_key)
            return {"statusCode": 409, "body": "New key already exists"}
        except s3.exceptions.ClientError:
            pass
        updates.append({
            "user": current_user,
            "time": datetime.utcnow().isoformat() + "Z",
            "action": f"rename to {new_key}"
        })
        try:
            put_object_with_metadata(new_key, old_content, owner, updates)
        except Exception as e:
            return {"statusCode": 500, "body": f"Failed to create new key: {str(e)}"}
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=old_key)
        except Exception as e:
            return {"statusCode": 500, "body": f"New created, but failed to delete old: {str(e)}"}
        return {"statusCode": 200, "body": "Rename successful"}
    return {"statusCode": 404, "body": "Not found"}

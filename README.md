# LeetCode Solutions

Auto-synced LeetCode solutions for [jithin-jz](https://leetcode.com/u/jithin-jz/)

![Sync LeetCode Solutions](https://github.com/jithin-jz/leetcode-solutions/actions/workflows/sync.yml/badge.svg)

## Structure

```
solutions/
├── 0001-two-sum/
│   ├── solution.py
│   └── README.md
├── 0002-add-two-numbers/
│   ├── solution.js
│   └── README.md
└── ...
```

## Setup

This repo uses a GitHub Action that runs daily at midnight to fetch accepted submissions from LeetCode and commit them automatically.

### Required Secrets

Add these in your repo → Settings → Secrets and variables → Actions:

- `LEETCODE_SESSION` — Your LeetCode session cookie
- `LEETCODE_CSRF_TOKEN` — Your LeetCode CSRF token

### How to get your LeetCode session cookie

1. Log in to [leetcode.com](https://leetcode.com)
2. Open browser DevTools (F12) → Application → Cookies → `https://leetcode.com`
3. Copy the value of `LEETCODE_SESSION`
4. Copy the value of `csrftoken`

> ⚠️ Session cookies expire periodically. You'll need to update the secret when sync stops working.

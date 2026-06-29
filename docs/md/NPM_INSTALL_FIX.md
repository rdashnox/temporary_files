# NPM Install Fix

If `npm install` tries to download from an internal OpenAI URL and shows `ETIMEDOUT`, delete any generated lock file and force npm to use the public npm registry.

From the frontend folder:

```powershell
cd frontend
rmdir /s /q node_modules
if (Test-Path package-lock.json) { del package-lock.json }
npm config set registry https://registry.npmjs.org/
npm cache clean --force
npm install
npm run dev
```

This project intentionally does not include `node_modules` or `package-lock.json` in the ZIP.

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\frontend"

npm config set registry https://registry.npmjs.org/

if (!(Test-Path "node_modules")) {
    npm install
}

npm run dev

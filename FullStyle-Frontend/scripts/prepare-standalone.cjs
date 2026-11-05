const { cpSync, existsSync, symlinkSync } = require('node:fs')
cpSync('.next/static', '.next/standalone/.next/static', { recursive: true })
if (existsSync('public'))
  cpSync('public', '.next/standalone/public', { recursive: true })
// /tmp is the existing tmpfs mount in the read-only local container.
symlinkSync('/tmp', '.next/standalone/.next/cache', 'dir')

const { cpSync } = require('node:fs');
cpSync('src/graphql/schemas', 'dist/graphql/schemas', {
  recursive: true,
  filter: (source) => !source.endsWith('.ts'),
});

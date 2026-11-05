import { readFileSync } from 'fs';
import path from 'path';
import { gql } from 'graphql-tag';

const authSchema = readFileSync(
  path.resolve(__dirname, 'auth.graphql'),
  'utf8',
);
const chatSchema = readFileSync(
  path.resolve(__dirname, 'chat.graphql'),
  'utf8',
);
const logicSchema = readFileSync(
  path.resolve(__dirname, 'logic.graphql'),
  'utf8',
);

export const typeDefs = gql`
  ${authSchema}
  ${chatSchema}
  ${logicSchema}
`;

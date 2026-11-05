import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { randomUUID } from 'node:crypto';
import resolvers from './graphql/resolvers';
import { typeDefs } from './graphql/schemas';

const server = new ApolloServer({
  plugins: [
    {
      async requestDidStart() {
        return {
          async willSendResponse({ response, contextValue }: any) {
            response.http?.headers.set(
              'X-Correlation-ID',
              contextValue.correlationId,
            );
            response.http?.headers.set(
              'X-Operation-ID',
              contextValue.operationId,
            );
          },
        };
      },
    },
  ],
  typeDefs,
  resolvers: resolvers as any,
});

startStandaloneServer(server, {
  context: async ({ req }) => {
    const token = req.headers.authorization || '';
    const safe = (value: unknown) =>
      typeof value === 'string' && /^[A-Za-z0-9._-]{1,80}$/.test(value)
        ? value
        : randomUUID();
    return {
      token,
      correlationId: safe(req.headers['x-correlation-id']),
      operationId: safe(req.headers['x-operation-id']),
    };
  },
}).then(({ url }) => {
  console.log(`🚀 GraphQL Gateway ready at ${url}`);
});

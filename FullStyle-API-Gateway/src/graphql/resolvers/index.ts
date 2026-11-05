import { tracing } from '../../tracing';
import { authResolvers } from './auth';
import { chatResolvers } from './chat';
import { logicResolvers } from './logic';
import { mergeResolvers } from '@graphql-tools/merge';

const resolvers = mergeResolvers([
  authResolvers,
  chatResolvers,
  logicResolvers,
]);

for (const operation of ['Query', 'Mutation']) {
  const fields = (resolvers as any)[operation];
  for (const [name, resolver] of Object.entries(fields)) {
    if (typeof resolver !== 'function') continue;
    fields[name] = (
      parent: unknown,
      args: unknown,
      context: any,
      info: unknown,
    ) =>
      tracing.run(
        {
          correlationId: context.correlationId,
          operationId: context.operationId,
        },
        () => resolver(parent, args, context, info),
      );
  }
}

export default resolvers;

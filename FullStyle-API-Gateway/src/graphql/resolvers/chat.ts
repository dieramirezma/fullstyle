import { ChatAPI } from '../../datasources/chatAPI';
import { ChatRequest } from '../../types/chat';

const chatAPI = new ChatAPI();

export const chatResolvers = {
  Mutation: {
    sendMessage: async (
      _: any,
      args: ChatRequest,
      { token }: { token: string },
    ) => {
      return await chatAPI.sendMessage(args, token);
    },
  },
};

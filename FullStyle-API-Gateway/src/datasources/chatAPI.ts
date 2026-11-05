import axios from 'axios';
import { ChatRequest, ChatResponse } from '../types/chat';
import { CHAT_BASE_URL } from '../config/constants';

export class ChatAPI {
  async sendMessage(input: ChatRequest, token: string): Promise<ChatResponse> {
    try {
      if (!token?.startsWith('Bearer '))
        throw new Error('Authenticated identity required');
      const response = await axios.post(
        `${CHAT_BASE_URL.replace(/\/$/, '')}/chat/send`,
        input,
        {
          headers: { Authorization: token },
          timeout: 25000,
        },
      );
      return response.data;
    } catch (error: any) {
      console.error(
        '❌ Chat API error:',
        error.response?.data || error.message,
      );
      throw new Error(error.response?.data?.detail || 'Failed to send message');
    }
  }
}

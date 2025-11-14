import { isRestConfigured, restClient } from './client';

export type ChangePasswordPayload = {
  current_password: string;
  new_password: string;
};

export const accountApi = {
  async changePassword(payload: ChangePasswordPayload): Promise<void> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para usar el backend REST');
    }
    await restClient.put('/auth/change-password', payload);
  },
};

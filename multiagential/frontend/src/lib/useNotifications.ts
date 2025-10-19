import { useEffect, useState } from 'react';
import { notificationManager } from './notifications';

export function useNotifications() {
  const [isSupported, setIsSupported] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const supported = notificationManager.isSupported();
    setIsSupported(supported);

    if (supported) {
      setPermission(notificationManager.getPermissionStatus());

      // Register service worker on mount
      notificationManager.registerServiceWorker().then(() => {
        setIsInitialized(true);
      });
    }
  }, []);

  const requestPermission = async () => {
    const granted = await notificationManager.requestPermission();
    setPermission(notificationManager.getPermissionStatus());
    return granted;
  };

  return {
    isSupported,
    permission,
    isInitialized,
    requestPermission,
    notificationManager,
  };
}

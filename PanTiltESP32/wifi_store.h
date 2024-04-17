//#include <sys/_intsup.h>
#ifndef wifi_store_h
#define wifi_store_h
#include <Preferences.h>
#include "Arduino.h"


class wifi_store
{
	public:
		String ssid;
    String password;
    wifi_store();
    bool begin(void);
    bool has_credentials(void);
    bool connect(void);
    void write_credentials(String, String);
    void manage_credentials(void);
	
	private:
		Preferences preferences;
};

#endif //wifi_store_h
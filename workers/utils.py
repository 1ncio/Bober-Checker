from fake_useragent import UserAgent

def get_formatted_proxy(proxy: str) -> dict:

    try:
        if '@' in proxy or len(proxy.split(':')) == 2:
            formatted_proxy = proxy

        else:
            parts = proxy.split(':')

            if '.' in parts[0]:
                formatted_proxy = ':'.join(parts[2:]) + '@' + ':'.join(parts[:2])

            else:
                formatted_proxy = ':'.join(parts[:2]) + '@' + ':'.join(parts[2:])
        
        return {
            'http': f'http://{formatted_proxy}',
            'https': f'http://{formatted_proxy}'
        }
    
    except:
        return None

def get_user_agent_() -> str:
    return UserAgent().random
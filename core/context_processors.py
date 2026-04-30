from .models import SiteConfig

def site_config(request):
    """
    Context processor para injetar a configuração global do site
    em todos os templates do projeto sob a variável 'site'.
    """
    site, _ = SiteConfig.objects.get_or_create(id=1)
    return {
        "site": site
    }

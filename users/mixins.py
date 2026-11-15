from onlinecourse.context_processors import get_role


class RoleTemplateMixin:
    page = None
    fallback_template = None

    def get_template_names(self):
        role = get_role(self.request.user)
        names = [f'onlinecourse/{role}/{self.page}.html']
        if self.fallback_template:
            names.append(self.fallback_template)
        return names

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = get_role(self.request.user)
        return context

class AnonymousPostAuthentication(BasicAuthentication):
    """ No auth on post / for user creation """

    def is_authenticated(self, request, **kwargs):
        """ If PATH and POST match your scenario, 
        don't check auth, otherwise fall back to parent """

        if request.path == "/xapi/navigate_master_query_pagination/" 
           and request.method == "POST" :
            return True
        else:
            return (super(AnonymousPostAuthentication,self)
                        .is_authenticated(request, **kwargs))
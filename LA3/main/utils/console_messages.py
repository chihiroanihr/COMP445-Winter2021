class HttpcManuals:

    LOGO = '''
     _     _   _              
    | |__ | |_| |_ _ __   ___ 
    | '_ \| __| __| '_ \ / __|
    | | | | |_| |_| |_) | (__ 
    |_| |_|\__|\__| .__/ \___|
                |_|         
    '''

    WELCOME = "!!! Welcome to httpc !!!\n"

    DESCRIPTION = "httpc is a tool for transferring data from or to a server." + \
        "It supposrts HTTP protocols. httpc offers useful tricks like HTTP GET and POST request. \
        \n\nhttpc is powered by libhttpc for all transfer-related features."

    HELP = "httpc is a curl-like application but supports HTTP protocols only. \
    \n\nUsage: \
    \n    httpc command [arguments] \
    \nThe commands are: \
    \n    get\texecutes a HTTP GET request and prints the response. \
    \n    post\texecutes a HTTP POST request and prints the response. \
    \n    help\tprints this screen. \
    "
    HELP_EPILOG = "Use \"httpc help [command]\" for more information about a command."

    URL_HELP = "Determines the targeted HTTP server. " + \
        "It could contain parameters of the HTTP operation."
    V_HELP = "Prints the detail of the response such as protocol, status, and headers."
    H_HELP = "Associates headers to HTTP Request with the format 'key:value'."
    D_HELP = "Associates an inline data to the body HTTP POST request."
    F_HELP = "Associates the content of a file to the body HTTP POST request."
    O_HELP = "Returns the body of the response to the specified file instead of the console."

    GET_HELP = "Get executes a HTTP GET reqeust for a given URL."
    POST_HELP = "Post executes a HTTP POST request for a given URL with inline data or form file."
    POST_EPILOG = "Either [-d] or [-f] can be used but not both."

    RH_HELP = "Set default router host"
    RP_HELP = "Set default router port"
    SH_HELP = "Set default server host"
    SP_HELP = "Set default server port"

    GET_HELP_CUSTOM = f"\
    \nUsage: httpc get [-v] [-h key:value] URL [-o output-file] FILENAME \
    \n \
    \nGet executes a HTTP GET reqeust for a given URL. \
    \n  -v              {V_HELP} \
    \n  -h key:value    {H_HELP} \
    \n \
    \nOptional configuration: \
    \n  -rh             {RH_HELP} \
    \n  -rp             {RP_HELP} \
    \n  -sh             {SH_HELP} \
    \n  -sv             {SP_HELP} \
    "

    POST_HELP_CUSTOM = f"\
    \nUsage: httpc post [-v] [-h key:value] [-d inline-data] [-f file] URL [-o output-file] FILENAME \
    \n \
    \nPost executes a HTTP POST request for a given URL with inline data or form file. \
    \n  -v              {V_HELP} \
    \n  -h key:value    {H_HELP} \
    \n  -d string       {D_HELP} \
    \n  -f file         {F_HELP} \
    \n \
    \nEither [-d] or [-f] can be used but not both. \
    \n \
    \nOptional configuration: \
    \n  -rh             {RH_HELP} \
    \n  -rp             {RP_HELP} \
    \n  -sh             {SH_HELP} \
    \n  -sv             {SP_HELP} \
    "


class HttpfsManuals:

    V_HELP = "Prints debugging messages."
    P_HELP = "Specifies the port number that the server will listen and serve at. \
    \n      Default is 8080."
    D_HELP = "Associates an inline data to the body HTTP POST request."

    HELP = f"httpfc is a simple file server. \
    \nUsage: httpfc [-v] [-p PORT] [-d PATH-TO-DIR] \
    \n  -v\t{V_HELP} \
    \n  -p\t{P_HELP} \
    \n  -d\t{D_HELP} \
    "


if __name__ == '__main__':
    print(HttpcManuals.LOGO)
    print(HttpcManuals.WELCOME)
    print(HttpcManuals.DESCRIPTION)
    print()
    print(HttpcManuals.EPILOG)
    print()
    print(HttpcManuals.HELP)
    print(HttpcManuals.HELP_EPILOG)
    print()
    print(HttpcManuals.GET_HELP_CUSTOM)
    print()
    print(HttpcManuals.POST_HELP_CUSTOM)
    print()
    print(HttpfsManuals.HELP)

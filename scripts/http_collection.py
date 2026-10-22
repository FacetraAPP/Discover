"""Structural checks for the portable HTTP collection extension.

Rhai expressions are checked as bounded text here; Facetra compiles/evaluates
them. This module never evaluates expressions or performs network requests.
"""
import re

def validate(value, context, check):
    mapping, text, number, identifier, require, json_value = check
    pagination = value.get("pagination")
    if pagination is not None:
        mapping(pagination, context+".pagination", {"initial","records","next","max_pages"}, {"initial","next"})
        mapping(pagination["initial"], context+".pagination.initial")
        json_value(pagination["initial"], context+".pagination.initial")
        for key in ("next","records"):
            if key in pagination:
                expression = text(pagination[key],context+".pagination."+key)
                require(len(expression.encode()) <= 4096,context,"expression exceeds 4096 bytes")
        number(pagination.get("max_pages",100),context+".pagination.max_pages",1,1000,integer=True)
        require(not (pagination.get("records") is not None and value.get("recordsPath")),context,"choose records or recordsPath")
    foreach = value.get("foreach")
    if foreach is not None:
        mapping(foreach,context+".foreach",{"source","max_items","include_item"},{"source"})
        identifier(foreach["source"],context+".foreach.source")
        number(foreach.get("max_items",1000),context+".foreach.max_items",1,10000,integer=True)
        require(type(foreach.get("include_item",False)) is bool,context,"include_item must be boolean")
    markup=value.get("format") in ("html","xml")
    require(markup == (value.get("extract") is not None),context,"HTML/XML require extract; JSON/CSV cannot use extract")
    if markup:
        extraction=value["extract"]
        mapping(extraction,context+".extract",{"rows","fields","context","namespaces"},{"rows","fields"})
        require(len(text(extraction["rows"],context).encode())<=1024,context,"row selector exceeds 1024 bytes")
        for name in ("fields","context"):
            fields=mapping(extraction.get(name,{}),context+".extract."+name)
            require((name!="fields" or len(fields)>0) and len(fields)<=128,context,"invalid extraction field count")
            for key,field in fields.items():
                identifier(key,context+".extract."+name)
                mapping(field,context,{"selector","attribute","all","required","json","resolve_url"},{"selector"})
                require(len(text(field["selector"],context).encode())<=1024,context,"field selector exceeds 1024 bytes")
                if "attribute" in field: text(field["attribute"],context)
                for flag in ("all","required","json","resolve_url"):
                    if flag in field: require(type(field[flag]) is bool,context,flag+" must be boolean")
                require(not(field.get("json") and field.get("resolve_url")),context,"json and resolve_url are exclusive")
        namespaces=mapping(extraction.get("namespaces",{}),context+".namespaces")
        require(len(namespaces)<=32 and (value["format"]=="xml" or not namespaces),context,"invalid namespaces")
        for prefix,uri in namespaces.items(): text(prefix,context); text(uri,context)
    if value.get("limits") is not None:
        limits=mapping(value["limits"],context+".limits",{"max_requests","max_bytes","max_rows","timeout_ms"})
        for key,maximum in {"max_requests":10000,"max_bytes":104857600,"max_rows":100000,"timeout_ms":300000}.items():
            if key in limits: number(limits[key],context+".limits."+key,1,maximum,integer=True)
    if value.get("retry") is not None:
        retry=mapping(value["retry"],context+".retry",{"max_attempts","delay_ms","retry_post"})
        number(retry.get("max_attempts",3),context,1,5,integer=True)
        number(retry.get("delay_ms",250),context,0,10000,integer=True)
        require(type(retry.get("retry_post",False)) is bool,context,"retry_post must be boolean")
        require(value.get("method","get").lower()!="post" or retry.get("retry_post") is True,context,"POST replay requires retry_post")

    dependencies=set(value.get("depends_on") or [])
    if foreach: require(foreach["source"] in dependencies,context,"foreach requires explicit depends_on")
    def walk(node, page):
        if isinstance(node,dict):
            for child in node.values(): walk(child,page)
        elif isinstance(node,list):
            for child in node: walk(child,page)
        elif isinstance(node,str):
            for token in re.findall(r"\{\{(.*?)\}\}",node,flags=re.S):
                path=token.split("|",1)[0].strip().split(".")
                if path[0]=="page": require(page,context,"page outside pagination")
                if path[0]=="item": require(foreach is not None,context,"item outside foreach")
                if path[0]=="sources":
                    require(len(path)>=2 and path[1] in dependencies,context,"source template requires explicit depends_on")
    for key in ("url","headers","params","json","data"): walk(value.get(key),pagination is not None)
    if pagination: walk(pagination["initial"],False)

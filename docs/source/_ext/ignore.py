from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective


class Ignore(nodes.Admonition, nodes.Element):
    pass


class IgnoreList(nodes.General, nodes.Element):
    pass


def visit_ignore_node(self, node):
    self.visit_admonition(node)


def depart_ignore_node(self, node):
    self.depart_admonition(node)


class IgnoreListDirective(Directive):
    def run(self):
        return [IgnoreList("")]


class IgnoreDirective(SphinxDirective):

    # this enables content in the directive
    has_content = True

    def run(self):
        targetid = "ignore-%d" % self.env.new_serialno("ignore")
        targetnode = nodes.target("", "", ids=[targetid])

        ignore_node = Ignore("\n".join(self.content))
        ignore_node += nodes.title(_("ignore"), _("ignore"))
        self.state.nested_parse(self.content, self.content_offset, ignore_node)

        if not hasattr(self.env, "ignore_all_ignores"):
            self.env.ignore_all_ignores = []

        self.env.ignore_all_ignores.append(
            {
                "docname": self.env.docname,
                "lineno": self.lineno,
                "ignore": ignore_node.deepcopy(),
                "target": targetnode,
            }
        )

        return [targetnode, ignore_node]


def purge_ignores(app, env, docname):
    if not hasattr(env, "ignore_all_ignores"):
        return

    env.ignore_all_ignores = [
        ignore for ignore in env.ignore_all_ignores if ignore["docname"] != docname
    ]


def merge_ignores(app, env, docnames, other):
    if not hasattr(env, "ignore_all_ignores"):
        env.ignore_all_ignores = []
    if hasattr(other, "ignore_all_ignores"):
        env.ignore_all_ignores.extend(other.ignore_all_ignores)


def process_ignore_nodes(app, doctree, fromdocname):
    if not app.config.include_ignores:
        for node in doctree.findall(Ignore):
            node.parent.remove(node)

    # Replace all ignorelist nodes with a list of the collected ignores.
    # Augment each ignore with a backlink to the original location.
    env = app.builder.env

    if not hasattr(env, "ignore_all_ignores"):
        env.ignore_all_ignores = []

    for node in doctree.findall(IgnoreList):
        if not app.config.include_ignores:
            node.replace_self([])
            continue

        content = []

        for ignore_info in env.ignore_all_ignores:
            para = nodes.paragraph()
            filename = env.doc2path(ignore_info["docname"], base=None)
            description = _(
                "(The original entry is located in %s, line %d and can be found "
            ) % (filename, ignore_info["lineno"])
            para += nodes.Text(description)

            # Create a reference
            newnode = nodes.reference("", "")
            innernode = nodes.emphasis(_("here"), _("here"))
            newnode["refdocname"] = ignore_info["docname"]
            newnode["refuri"] = app.builder.get_relative_uri(
                fromdocname, ignore_info["docname"]
            )
            newnode["refuri"] += "#" + ignore_info["target"]["refid"]
            newnode.append(innernode)
            para += newnode
            para += nodes.Text(".)")

            # Insert into the ignorelist
            content.append(ignore_info["ignore"])
            content.append(para)

        node.replace_self(content)


def setup(app):
    app.add_config_value("include_ignores", False, "html")

    app.add_node(IgnoreList)
    app.add_node(
        Ignore,
        html=(visit_ignore_node, depart_ignore_node),
        latex=(visit_ignore_node, depart_ignore_node),
        text=(visit_ignore_node, depart_ignore_node),
    )

    app.add_directive("ignore", IgnoreDirective)
    app.add_directive("ignorelist", IgnoreListDirective)
    app.connect("doctree-resolved", process_ignore_nodes)
    app.connect("env-purge-doc", purge_ignores)
    app.connect("env-merge-info", merge_ignores)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

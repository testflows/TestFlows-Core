function chart() {
    var chart = {};
    const width = 950,
        height = 800;

    const svg = d3.select("#map-chart").append("svg")
        .attr("viewBox", [-width / 2, -height / 2, width, height])
        .style("font", "12px sans-serif");

    const marker_selection = svg.append("defs");

    const link_selection = svg.append("g")
          .attr("fill", "none")
          .attr("stroke-width", 1.5);

    const node_selection = svg.append("g")
          .attr("fill", "currentColor")
          .attr("stroke-linecap", "round")
          .attr("stroke-linejoin", "round");

    var links = %(links)s;
    var types = Array.from(new Set(links.map(d => d.type)));
    var nodes = Array.from(new Set(%(nodes)s));
    var data = {nodes: nodes, links: links};

    const simulation = d3.forceSimulation()
         .force("link", d3.forceLink().id(d => d.id))
         .force("charge", d3.forceManyBody().strength(-1400))
         .force("x", d3.forceX())
         .force("y", d3.forceY());

    simulation.on("tick", () => {
         link_selection.selectAll("path").attr("d", linkArc);
         node_selection.selectAll("g").attr("transform", d => `translate(${d.x},${d.y})`);
    });

    data.nodes_id_to_node = {};
    data.nodes.forEach(function(node) {
         data.nodes_id_to_node[node.id] = node;
    });

    var graph_links = data.links.map(d => Object.create(d));
    var graph_nodes = data.nodes.map(d => Object.create(d));
    var graph_types = Array.from(types);
    var graph_highlight_paths = [];

    graph_types.push("visited");

    function update() {
        simulation.nodes(graph_nodes);
        simulation.force("link").links(graph_links);

        const marker = marker_selection.selectAll("marker").data(graph_types)
            .join("marker")
            .attr("id", d => `arrow-${d}`)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 33)
            .attr("refY", -2.5)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", d => color_type(d))
            .attr("d", "M0,-5L10,0L0,5");

        const link = link_selection.selectAll("path").data(graph_links, d => d.source + d.target);

        link.attr("stroke", d => color_type(d.type))
            .attr("marker-end", d => `url(${new URL(`#arrow-${d.type}`, location)})`);

        link.exit().remove();

        const enter_links = link.enter();
        enter_links.append("path")
            .attr("stroke", d => color_type(d.type))
            .attr("marker-end", d => `url(${new URL(`#arrow-${d.type}`, location)})`);

        const node = node_selection.selectAll("g").data(graph_nodes, d => d.id);

        node.selectAll("circle")
            .attr("fill", d => color_node(d));

        node.exit().remove();

        const enter_nodes = node.enter();
        const nodes_elem = enter_nodes.append("g")
            .on("click", node_click)
            .call(drag(simulation));

        nodes_elem.append("circle")
            .attr("stroke", "#b5b5fb")
            .attr("fill", d => color_node(d))
            .attr("stroke-width", 1.5)
            .attr("r", 20);

        nodes_elem.append("text")
            .attr("x", 25)
            .attr("y", "0.31em")
            .text(d => d.name)
            .clone(true).lower()
            .attr("fill", "none")
            .attr("stroke", "white")
            .attr("stroke-width", 3);

        simulation.alpha(0.25).restart();
    };

    function highlight(paths) {
        if (!paths)
            return;

        graph_highlight_paths = paths;

        var highlight_nodes = new Set();
        var highlight_links = new Set();

        paths.forEach(function(path) {
            path.path.nodes.forEach(function(n) {
                highlight_nodes.add(n);
            });
            path.path.links.forEach(function(l) {
                highlight_links.add(l.source + '/' + l.target);
            });
        });

        graph_nodes.forEach(function(node) {
            if (highlight_nodes.has(node.id)) {
                node.type = "visited";
            }
            else {
                node.type = "unvisited";
            }
        });

        if (window.debug) {
            console.log("highlight links:")
            highlight_links.forEach(function(l) {
                e = l.split("/");
                console.log(e, data.nodes_id_to_node[e[0]], data.nodes_id_to_node[e[1]])
                console.log(data.nodes_id_to_node[e[0]].name, " -> ", data.nodes_id_to_node[e[1]].name);
            });
        }

        graph_links.forEach(function(link) {
            if (!link.id)
                link.id = link.source.id + '/' + link.target.id;
            if (!link._type)
                link._type = link.type

            if (highlight_links.has(link.id)) {
                link.type = "visited";
                if (window.debug)
                    console.log(data.nodes_id_to_node[link.source.id].name, " -> ", data.nodes_id_to_node[link.target.id].name);
            }
            else {
                link.type = link._type;
            }
        });

        update();
    };

    chart.update = update;
    chart.highlight = highlight;

    function node_click(d) {
        if (d3.event.defaultPrevented)
            return; // ignore drag

        var node = graph_nodes[d.index];

        if (node.children.nodes.length > 0) {
            var node_id_to_index = {}
            graph_nodes.forEach(function(node) {
                node_id_to_index[node.id] = node.index;
            });

            if (node.collapsed) {
                graph_nodes = graph_nodes.concat(node.children.nodes.map(function(id) {
                    var obj = Object.create(data.nodes_id_to_node[id]);
                    if (obj.children.nodes)
                        obj.collapsed = true;
                    return obj;
                }));
                graph_links = graph_links.concat(node.children.links.map(d => Object.create(d)));
                node.collapsed = false;
            }
            else {
                var children = new Set();
                function find_all_children(node) {
                    if (children.has(node)) return;
                    if (node.children) {
                        node.children.nodes.forEach(function(child) {
                            if (child in node_id_to_index) {
                                find_all_children(graph_nodes[node_id_to_index[child]]);
                                children.add(node_id_to_index[child]);
                            }
                        });
                    }
                }
                find_all_children(node);
                Array.from(children).sort((a, b) => b - a).forEach(index => graph_nodes.splice(index, 1));
                graph_links = graph_links.filter(link => !(children.has(link.source.index) || children.has(link.target.index)));
                node.collapsed = true;
            }
            update();
            highlight(graph_highlight_paths);
        }
    }

    var color_node = function(d) {
        if (d.type == "visited") {
            return "mediumspringgreen";
        }
        if (d.children.nodes.length > 0) {
            return "#ffd8fd";
        }
        return "white";
    };

    var color_type = function(type) {
        if (type == "link") {
            return "blue";
        }
        else if (type == "visited")  {
            return "mediumspringgreen";
        }
        return "orange";
    };

    function linkArc(d) {
        const r = Math.hypot(d.target.x - d.source.x, d.target.y - d.source.y);
        return `
            M${d.source.x},${d.source.y}
            A${r},${r} 0 0,1 ${d.target.x},${d.target.y}
        `;
    }

    var drag = function(simulation) {
        function dragstarted(d) {
            if (!d3.event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(d) {
            d.fx = d3.event.x;
            d.fy = d3.event.y;
        }

        function dragended(d) {
            if (!d3.event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);
    };

    chart.update();
    return chart;
}

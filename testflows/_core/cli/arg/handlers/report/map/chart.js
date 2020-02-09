function chart() {
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
         .force("charge", d3.forceManyBody().strength(-2400))
         .force("x", d3.forceX())
         .force("y", d3.forceY());

    simulation.on("tick", () => {
         link_selection.selectAll("path").attr("d", linkArc);
         node_selection.selectAll("g").attr("transform", d => `translate(${d.x},${d.y})`);
    });

    var graph_links = data.links.map(d => Object.create(d));
    var graph_nodes = data.nodes.map(d => Object.create(d));

    function update() {
        simulation.nodes(graph_nodes);
        simulation.force("link").links(graph_links);

        const marker = marker_selection.selectAll("marker").data(types)
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
        link.exit().remove();

        const enter_links = link.enter();
        enter_links.append("path")
            .attr("stroke", d => color_type(d.type))
            .attr("marker-end", d => `url(${new URL(`#arrow-${d.type}`, location)})`);

        const node = node_selection.selectAll("g").data(graph_nodes, d => d.id);
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
    };

    function node_click(d) {
        if (d3.event.defaultPrevented)
            return; // ignore drag

        var node = graph_nodes[d.index];
        console.log(node);
        if (node.children.length > 0) {
            var node_id_to_index = {}
            graph_nodes.forEach(function(node) {
                node_id_to_index[node.id] = node.index;
            });

            var children = new Set();
            function find_all_children(node) {
                if (children.has(node.index)) return;
                node.children.forEach(function(child) {
                    if (child in node_id_to_index) {
                        find_all_children(graph_nodes[node_id_to_index[child]]);
                        children.add(node_id_to_index[child]);
                    }
                });
            }
            find_all_children(node);
            Array.from(children).sort((a, b) => b - a).forEach(index => graph_nodes.splice(index, 1));
            graph_links = graph_links.filter(link => !(children.has(link.source.index) || children.has(link.target.index)));
            update();
        }
    }

    var color_node = function(d) {
        if (d.children.length > 0) {
            return "#ffd8fd";
        }
        return "white";
    };

    var color_type = function(type) {
        if (type == "link") {
            return "blue";
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

    update();
}

window.onload = function() {
  chart();
};

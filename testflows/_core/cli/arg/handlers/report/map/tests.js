function label_click(d) {
    var elem = d3.select(this);
    var parent = d3.select(this.parentNode);
    if (d3.event.defaultPrevented)
        return;
    parent.classed("active", parent.classed("active") ? false : true);
    window.chart.highlight(d3.select("#tests-list").selectAll("label.active").data());
}

function tests() {
    var paths = %(paths)s;
    if (window.debug)
        console.log("paths:", paths);

    const div = d3.select("#tests-list").append("div");
    const label = div.selectAll("label").data(paths);

    const enter_labels = label.enter();

    const labels_elem = enter_labels.append("label")
        .classed("container", true)
        .text(d => d.test);

    labels_elem.append("input")
        .attr("type", "checkbox")
        .on("click", label_click);

    labels_elem.append("span").classed("checkmark", true);
}
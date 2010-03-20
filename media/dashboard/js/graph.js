
function plot_graph(placeholder, data, dataurl, options, refresh_rate, element_id) {
    /*
    Replace the jQuery placeholder object with a graph. The graph displays the given data (array of dictionaries)
    depending on the options (dictionary) given. If refresh_rate > 0, automatically refresh the object after
    refresh_rate seconds.
    NOTE: element_id is not used at the moment.
    */

    plot_graph_jqplot(placeholder, data, dataurl, options, refresh_rate, element_id);
}

function plot_graph_jqplot(placeholder, data, dataurl, options, refresh_rate, element_id) {
    /*
    Plot the data using the jqPlot JS graphing library.
    */

    if (options['bars'] != undefined) {
	options['seriesDefaults'] = {renderer: $.jqplot.BarRenderer, rendererOptions: { barPadding: 8, barMargin: 20}};
    }
    var graph = null;

    function fetch_data() {
	function update_options(data, options) {
	    if (data['empty_series'] == true) {
		options['legend']['show'] = false;
		placeholder.css('height', '200px');
	    }
	    else {
                options['series'] = data['series'];
	    }

	    if (data['non_integer'] == false) {
		options['axes']['yaxis']['tickOptions'] = {formatString:'%.0f'};
	    }

	    // Set up the x-axis renderer
	    if (options['bars'] != undefined) {
	        options['axes']['xaxis']['renderer'] = $.jqplot.CategoryAxisRenderer;
		options['axes']['xaxis']['ticks'] = data['ticks'];
	    }
	    else {
		// in elm_graph.html DateAxisRenderer is used iff x-axis type is datetime, else leave empty
	    }
	    return options
	}

	function plot_element(id, data, options) {
	    $('#' + id).empty();
            if (graph == null) {
		// Do stuff on initiation
	    }
	    try {
	        graph = $.jqplot(id, data, options);
	    }
	    catch(error) {
		ifconsole("Error on starting the plot with the given data and options");
	        ifconsole(error[0]);
	    }		    
        }


        function on_data_received(data) {
            plot_data = data['data'];
	    ifconsole(data);
	    ifconsole(plot_data);
	    ifconsole(options);
	    try {
		options = update_options(data, options);
	    }
	    catch(error) {
		ifconsole("Error on updating the options from the data received");
		ifconsole(error);
	    }
	    plot_element(placeholder[0].id, plot_data, options)

            if (refresh_rate != 0) { // refresh_rate is in seconds, timeout delay in milliseconds
            	setTimeout(fetch_data, refresh_rate * 1000);
	    }
         }
        
        $.ajax({
            url: dataurl,
            method: 'GET',
            dataType: 'json',
            success: on_data_received
        });
    }
    fetch_data(); // on_load, read in the data
}
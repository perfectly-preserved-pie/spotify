var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

// Define the custom cell renderer functions
// These functions will be used in the column definitions
// This function displays the artist or track name with a thumbnail
dagcomponentfuncs.ArtistOrTrackWithThumbnail = function (params) {
    var smallImageUrl = params.data.images_small;
    var artistName = params.value;  // this is because the cell field is "name"

    return React.createElement(
        'div',
        {
            style: {
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
            },
        },
        React.createElement(
            'img',
            {
                style: {width: '50px', height: 'auto', marginRight: '10px'},
                src: smallImageUrl
            }
        ),
        React.createElement(
            'span',
            null,
            artistName
        )
    );
};
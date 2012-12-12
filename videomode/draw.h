enum mode
{
    BLACK,
    INTRO,
    HIGHSCORE,
    CREDITS,
    TITLE,
    GAME,
    WOOD,
    SELECT,
    HOUSE,
    FIRE,
    ENTRY,
};

enum selection
{
    SELECTED_NONE,
    SELECTED_HOUSE,
    SELECTED_FIRE,
};

struct animation
{
    int play;
    int loop;
    int color;
    uint8_t length;
    uint8_t frame;
    GLuint *textures;
    GLfloat vertices[16];
    GLubyte *indices;
    GLuint vertex_buffer;
    GLuint index_buffer;
};

void draw();
void draw_init(unsigned width, unsigned height);
void draw_command(const char *animation);

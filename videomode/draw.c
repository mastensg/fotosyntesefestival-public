#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <math.h>
#include <err.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#ifdef USE_GLEW
#include <GL/glew.h>
#include <GL/gl.h>
#else
#include <GLES2/gl2.h>
#endif

#include "draw.h"

unsigned sw;
unsigned sh;

enum mode mode = INTRO;
enum selection selected = SELECTED_NONE;
char entry[3] = "   ";
char highscores[12 * 4] = "AAA BBB CCC DDD EEE FFF GGG HHH III JJJ KKK LLL ";
int move_house = 0;
int move_fire = 0;
int balls = 0;
int co2 = 0;
int sunshine = 0;
int water = 0;
int level = 1;
int fading_in_game = 0;
int fading_in_intro = 0;

GLuint program;
GLint resolution_uniform;
GLint offset_uniform;
GLint texture_uniform;
GLint fade_uniform;
GLint opacity_uniform;
GLint position_attrib;
GLint texcoord_attrib;

struct animation balls_anim;
struct animation bg_anim;
struct animation char_anim;
struct animation co2_anim;
struct animation credits_anim;
struct animation fireS_anim;
struct animation fire_anim;
struct animation highscore_anim;
struct animation houseS_anim;
struct animation house_anim;
struct animation intro_anim;
struct animation start_anim;
struct animation subtitle_anim;
struct animation sun_anim;
struct animation titleS_anim;
struct animation wat_anim;
struct animation wood_anim;

static const char *
gl_strerror(GLint error)
{
    switch(error)
    {
    case GL_NO_ERROR:
        return "GL_NO_ERROR, No error has been recorded.";
        break;
    case GL_INVALID_ENUM:
        return "GL_INVALID_ENUM, An unacceptable value is specified for an enumerated argument. The offending command is ignored and has no other side effect than to set the error flag.";
        break;

    case GL_INVALID_VALUE:
        return "GL_INVALID_VALUE, A numeric argument is out of range. The offending command is ignored and has no other side effect than to set the error flag.";
        break;

    case GL_INVALID_OPERATION:
        return "GL_INVALID_OPERATION, The specified operation is not allowed in the current state. The offending command is ignored and has no other side effect than to set the error flag.";
        break;

    case GL_INVALID_FRAMEBUFFER_OPERATION:
        return "GL_INVALID_FRAMEBUFFER_OPERATION, The command is trying to render to or read from the framebuffer while the currently bound framebuffer is not framebuffer complete (i.e. the return value from glCheckFramebufferStatus is not GL_FRAMEBUFFER_COMPLETE). The offending command is ignored and has no other side effect than to set the error flag.";
        break;

    case GL_OUT_OF_MEMORY:
        return "GL_OUT_OF_MEMORY, There is not enough memory left to execute the command. The state of the GL is undefined, except for the state of the error flags, after this error is recorded.";
        break;
    default:
        return "Unknown EGL error.";
    }
}

static void *
map_file(const char *path, off_t *numbytes) {
    int fd;
    void *p;

    if(-1 == (fd = open(path, O_RDONLY)))
        err(EXIT_FAILURE, "open(\"%s\")", path);

    if(-1 == (*numbytes = lseek(fd, 0, SEEK_END)))
        err(EXIT_FAILURE, "lseek");

    if(MAP_FAILED == (p = mmap(NULL, *numbytes, PROT_READ, MAP_SHARED, fd, 0)))
        err(EXIT_FAILURE, "mmap");

    close(fd);

    return p;
}

static GLuint
load_shader(GLenum type, const char *path)
{
    GLuint shader;
    GLint compiled;
    char *source;
    off_t source_len;

    if(0 == (shader = glCreateShader(type)))
        errx(EXIT_FAILURE, "glCreateShader: %s", gl_strerror(glGetError()));

    source = map_file(path, &source_len);

    glShaderSource(shader, 1, (const GLchar **)&source, (GLint *)&source_len);

    if(-1 == munmap(source, source_len))
        err(EXIT_FAILURE, "munmap");

    glCompileShader(shader);

    glGetShaderiv(shader, GL_COMPILE_STATUS, &compiled);

    if(!compiled)
    {
        GLint infolen = 0;

        glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &infolen);

        if(infolen > 1)
        {
            char *infolog = calloc(infolen, sizeof(char));

            glGetShaderInfoLog(shader, infolen, NULL, infolog);

            fprintf(stderr, "shader compilation:\n%s\n", infolog);

            free(infolog);
        }

        glDeleteShader(shader);

        exit(EXIT_FAILURE);
    }

    return shader;
}

static GLuint
load_program(const char *vs_path, const char *fs_path)
{
    GLuint program;
    GLuint vertex_shader;
    GLuint fragment_shader;
    GLint linked;

    vertex_shader = load_shader(GL_VERTEX_SHADER, vs_path);
    fragment_shader = load_shader(GL_FRAGMENT_SHADER, fs_path);

    if(0 == (program = glCreateProgram()))
        errx(EXIT_FAILURE, "glCreateProgram: %s", gl_strerror(glGetError()));

    glAttachShader(program, vertex_shader);
    glAttachShader(program, fragment_shader);

    glLinkProgram(program);

    glGetProgramiv(program, GL_LINK_STATUS, &linked);

    if(!linked)
    {
        GLint infolen = 0;

        glGetProgramiv(program, GL_INFO_LOG_LENGTH, &infolen);

        if(infolen > 1)
        {
            char *infolog = calloc(infolen, sizeof(char));

            glGetProgramInfoLog(program, infolen, NULL, infolog);

            fprintf(stderr, "shader linking:\n%s\n", infolog);

            free(infolog);
        }

        glDeleteProgram(program);

        exit(EXIT_FAILURE);
    }

    return program;
}

static GLubyte quad_indices[] = {
    2, 1, 0,
    0, 3, 2,
};

static void
load_animation(struct animation *a, const char *path)
{
    unsigned char *vma;
    off_t vma_len;
    int i;
    uint32_t w, h;
    GLubyte *p;
    static const GLfloat vertices[16] = {0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1};

    GLuint
    load_texture(GLsizei w, GLsizei h, GLubyte *pixels)
    {
        GLuint texture;

        glGenTextures(1, &texture);
        glBindTexture(GL_TEXTURE_2D, texture);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels);

        return texture;
    }

    fprintf(stderr, "%s...", path);

    vma = map_file(path, &vma_len);

    a->length = vma[0];

    if(!(a->textures = calloc(a->length, sizeof(GLuint))))
        err(EXIT_FAILURE, "calloc a->length, sizeof(GLuint)");

    w = (vma[1] << 8) | vma[2];
    h = (vma[3] << 8) | vma[4];

    fprintf(stderr, " %dx%d", w, h);

    p = &vma[5];

    for(i = 0; i < a->length; ++i)
    {
        a->textures[i] = load_texture(w, h, p);
        p += w * h * 4;
    }

    if(-1 == munmap(vma, vma_len))
        err(EXIT_FAILURE, "munmap %s", path);

    a->color = 1;
    a->frame = 0;

    memcpy(&a->vertices, vertices, sizeof(vertices));

    a->vertices[4] = w;
    a->vertices[8] = w;
    a->vertices[9] = h;
    a->vertices[13] = h;

    a->indices = quad_indices;

    glGenBuffers(1, &a->vertex_buffer);
    glBindBuffer(GL_ARRAY_BUFFER, a->vertex_buffer);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), a->vertices, GL_STATIC_DRAW);

    glGenBuffers(1, &a->index_buffer);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, a->index_buffer);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(quad_indices), quad_indices, GL_STATIC_DRAW);

    fprintf(stderr, ".\n");
}

void
draw_init(unsigned width, unsigned height)
{
    int i;

    width = 1280;
    height = 768;

    sw = width;
    sh = height;

#ifdef USE_GLEW
    GLenum glew_status;

    if(GLEW_OK != (glew_status = glewInit()))
        errx(EXIT_FAILURE, "glewInit: %s", glewGetErrorString(glew_status));

    fprintf(stderr, "GLEW   %s\n", glewGetString(GLEW_VERSION));
    fprintf(stderr, "OpenGL %d.%d\n", GLEW_VERSION_MAJOR, GLEW_VERSION_MINOR);
#endif

    program = load_program("vertex.glsl", "fragment.glsl");

    glUseProgram(program);

    resolution_uniform = glGetUniformLocation(program, "resolution");
    offset_uniform = glGetUniformLocation(program, "offset");
    texture_uniform = glGetUniformLocation(program, "texture");
    fade_uniform = glGetUniformLocation(program, "fade");
    opacity_uniform = glGetUniformLocation(program, "opacity");
    position_attrib = glGetAttribLocation(program, "position");
    texcoord_attrib = glGetAttribLocation(program, "texcoord");

    load_animation(&balls_anim, "ballz.vma");
    load_animation(&bg_anim, "bg.vma");
    load_animation(&char_anim, "char.vma");
    load_animation(&co2_anim, "co2.vma");
    load_animation(&credits_anim, "credits.vma");
    load_animation(&fire_anim, "fire.vma");
    load_animation(&fireS_anim, "fireS.vma");
    load_animation(&highscore_anim, "highscore.vma");
    load_animation(&house_anim, "house.vma");
    load_animation(&houseS_anim, "houseS.vma");
    load_animation(&intro_anim, "intro.vma");
    load_animation(&start_anim, "start.vma");
    load_animation(&subtitle_anim, "subtitle.vma");
    load_animation(&sun_anim, "sun.vma");
    load_animation(&titleS_anim, "titleS.vma");
    load_animation(&wat_anim, "wat.vma");
    load_animation(&wood_anim, "wood.vma");

    intro_anim.play = 1;
    intro_anim.loop = 1;
    start_anim.play = 1;
    start_anim.loop = 1;

    fire_anim.play = 1;
    fire_anim.loop = 1;
    house_anim.play = 1;
    house_anim.loop = 1;

    glViewport(0, 0, width, height);

    glUniform2f(offset_uniform, width, height);

    glEnable(GL_CULL_FACE);

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    glActiveTexture(GL_TEXTURE0);
    glUniform1i(texture_uniform, 0);

    glEnableVertexAttribArray(position_attrib);
    glEnableVertexAttribArray(texcoord_attrib);
}

static void
draw_frame(struct animation *anim, int x, int y, int frame)
{
    if(anim->color)
        glUniform1f(fade_uniform, 1.0);
    else
        glUniform1f(fade_uniform, fminf(anim->frame / 5.0, 1.0));

    glUniform2f(offset_uniform, x, y);

    glBindTexture(GL_TEXTURE_2D, anim->textures[frame]);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, anim->index_buffer);
    glBindBuffer(GL_ARRAY_BUFFER, anim->vertex_buffer);
    glVertexAttribPointer(position_attrib, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), 0);
    glVertexAttribPointer(texcoord_attrib, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), (GLvoid *)(2 * sizeof(GLfloat)));
    glDrawElements(GL_TRIANGLES, sizeof(quad_indices) / sizeof(quad_indices[0]), GL_UNSIGNED_BYTE, 0);
}

void
screenshot()
{
    uint8_t *pixels;
    FILE *f;

    if(!(pixels = calloc(3 * sw * sh, sizeof(pixels[0]))))
        err(EXIT_FAILURE, "calloc pixels");

    glReadPixels(0, 0, sw, sh, GL_RGB, GL_UNSIGNED_BYTE, pixels);

    if(!(f = fopen("screenshot.tga", "w")))
        err(EXIT_FAILURE, "fopen");

    tga_write(f, pixels, sw, sh);

    if(EOF == fclose(f))
        err(EXIT_FAILURE, "fclose");

    free(pixels);
}

void
draw_command(const char *animation)
{
    if(animation[0] == 'B' && strlen(animation) == 2)
    {
        balls = animation[1] - '0';
    }
    else if(animation[0] == 'C' && strlen(animation) == 5)
    {
        level = animation[1] - '0';
        co2 = animation[2] - '0';
        sunshine = animation[3] - '0';
        water = animation[4] - '0';

        co2_anim.color = co2 == level;
        sun_anim.color = sunshine == level;
        wat_anim.color = water == level;
    }
    else if(animation[0] == 'E' && strlen(animation) == 1 + 3)
    {
        strcpy(entry, animation + 1);
    }
    else if(animation[0] == 'H' && strlen(animation) == 1 + 12 * 4)
    {
        strcpy(highscores, animation + 1);
    }
    else if(!strcmp("screenshot", animation))
    {
        screenshot();
    }
    else if(!strcmp("black", animation))
    {
        mode = BLACK;
    }
    else if(!strcmp("intro", animation) && mode != INTRO)
    {
        mode = INTRO;

        intro_anim.frame = 0;
    }
    else if(!strcmp("highscore", animation))
    {
        mode = HIGHSCORE;
    }
    else if(!strcmp("credits", animation))
    {
        mode = CREDITS;
    }
    else if(!strcmp("title", animation) && mode != TITLE)
    {
        mode = TITLE;

        intro_anim.frame = 0;
    }
    else if(!strcmp("game", animation))
    {
        mode = GAME;
    }
    else if(!strcmp("wood", animation))
    {
        mode = WOOD;

        wood_anim.frame = 0;
        wood_anim.play = 1;
    }
    else if(!strcmp("select", animation))
    {
        mode = SELECT;

        selected = SELECTED_NONE;
    }
    else if(!strcmp("house", animation))
    {
        selected = SELECTED_HOUSE;
    }
    else if(!strcmp("fire", animation))
    {
        selected = SELECTED_FIRE;
    }
    else if(!strcmp("entry", animation))
    {
        mode = ENTRY;
    }
    else if(!strcmp("co2", animation))
    {
        co2_anim.frame = 0;
        co2_anim.play = 1;
    }
    else if(!strcmp("sunshine", animation))
    {
        sun_anim.frame = 0;
        sun_anim.play = 1;
    }
    else if(!strcmp("water", animation))
    {
        wat_anim.frame = 0;
        wat_anim.play = 1;
    }
}

void
draw()
{
    static unsigned char_fade_t = 0;
    static unsigned jiffies = 0;
    static float black_opacity = 1.0;
    static float intro_opacity = 0.0;
    static float highscore_opacity = 0.0;
    static float credits_opacity = 0.0;
    static float title_opacity = 0.0;
    static float game_opacity = 0.0;
    static float wood_opacity = 0.0;
    static float select_opacity = 0.0;
    static float select_t = 0.0;
    static float house_opacity = 0.0;
    static float fire_opacity = 0.0;
    static float entry_opacity = 0.0;

    void increment(struct animation *anim)
    {
        if(!anim->play || ++anim->frame < anim->length)
            return;

        anim->frame = 0;

        if(!anim->loop)
            anim->play = 0;
    }

    void fade(float *opacity, enum mode m)
    {
        if(mode == m && *opacity < 1.0)
            *opacity += 0.02;
        else if(*opacity > 0.0)
            *opacity -= 0.02;
    }

    GLuint char_index(char c)
    {
        if(c == '/')
            return 39;

        if(c >= '0' && c <= '9')
            return c - '0';

        if(c >= 'a' && c <= '}')
            c -= 'a' - 'A';

        if(c >= 'A' && c <= ']')
            return c - 'A' + 10;

        return 0;
    }

    glClearColor(0, 0, 0, 1);
    glClear(GL_COLOR_BUFFER_BIT);

    if(black_opacity < 1.0)
    {
        glUniform1f(opacity_uniform, 1.0 - black_opacity);
        draw_frame(&bg_anim, 0, 0, 0);
    }

    if(intro_opacity > 0.0)
    {
        glUniform1f(opacity_uniform, intro_opacity);
        draw_frame(&intro_anim, 0, 0, intro_anim.frame);

        glUniform1f(opacity_uniform, 8.0 * intro_opacity - 7.0);
        draw_frame(&start_anim, 0, 660, start_anim.frame);
    }

    if(intro_anim.frame == 0 && intro_opacity > 0.5)
        intro_anim.play = 1;

    if(highscore_opacity > 0.0)
    {
        char *p = highscores;
        char c;
        int i, j;

        glUniform1f(opacity_uniform, highscore_opacity);
        draw_frame(&highscore_anim, 0, 0, 0);

        glUniform1f(opacity_uniform, fminf(highscore_opacity, 0.9 + 0.1 * sin(++char_fade_t / 20.)));

        for(i = 0; i < 3; ++i)
            for(j = 0; j < 4 * 4; ++j)
                if(' ' != (c = *p++))
                    draw_frame(&char_anim, 62 + 77 * j, 140 + 190 * i, char_index(c));
    }

    if(credits_opacity > 0.0)
    {
        glUniform1f(opacity_uniform, credits_opacity);
        draw_frame(&credits_anim, 0, 0, 0);
    }

    if(title_opacity > 0.0)
    {
        glUniform1f(opacity_uniform, title_opacity);
        draw_frame(&intro_anim, 0, 0, intro_anim.frame);
    }

    if(intro_anim.frame == 0 && title_opacity > 0.5)
        intro_anim.play = 1;

    if(game_opacity > 0.0)
    {
        glUniform1f(opacity_uniform, game_opacity);
        draw_frame(&co2_anim, 22, 22, co2_anim.frame);
        draw_frame(&sun_anim, 437, 22, sun_anim.frame);
        draw_frame(&wat_anim, 863, 22, wat_anim.frame);

        draw_frame(&titleS_anim, 21, 590, 0);
        draw_frame(&balls_anim, 866, 600, balls);

        glUniform1f(opacity_uniform, fminf(game_opacity, 0.75 + 0.25 * sin(++char_fade_t / 20.)));
        draw_frame(&char_anim, 92, 350, co2);
        draw_frame(&char_anim, 169, 350, char_index('/'));
        draw_frame(&char_anim, 246, 350, level);
        draw_frame(&char_anim, 525, 350, sunshine);
        draw_frame(&char_anim, 602, 350, char_index('/'));
        draw_frame(&char_anim, 679, 350, level);
        draw_frame(&char_anim, 943, 350, water);
        draw_frame(&char_anim, 1020, 350, char_index('/'));
        draw_frame(&char_anim, 1097, 350, level);
    }

    if(wood_opacity > 0.0)
    {
        glUniform1f(opacity_uniform, wood_opacity);
        draw_frame(&wood_anim, 385, 50, wood_anim.frame);
    }

    if(select_opacity > 0.0)
    {
        glUniform1f(opacity_uniform, select_opacity);

        float offset = 330 * select_t * select_t * (3 - 2 * select_t);

        if(selected == SELECTED_NONE)
        {
            draw_frame(&houseS_anim, 50, 50, 0);
            draw_frame(&fireS_anim, 700, 50, 0);
            draw_frame(&subtitle_anim, 0, 573, 0);
        }
        else if(selected == SELECTED_HOUSE)
        {
            draw_frame(&house_anim, 50 + offset, 50, house_anim.frame);
            draw_frame(&fireS_anim, 700 + 1.8 * offset, 50, 0);
            draw_frame(&subtitle_anim, 0, 573, 2);
        }
        else if(selected == SELECTED_FIRE)
        {
            draw_frame(&houseS_anim, 50 - 1.8 * offset, 50, 0);
            draw_frame(&fire_anim, 700 - offset, 50, fire_anim.frame);
            draw_frame(&subtitle_anim, 0, 573, 1);
        }

        if(selected != SELECTED_NONE && select_t < 1.0)
            select_t += 0.02;
    }
    else
    {
        select_t = 0.0;
    }

    if(entry_opacity > 0.0)
    {
        char *p = entry;
        float o = fminf(entry_opacity, 0.9 + 0.1 * sin(++char_fade_t / 20.));
        int i;

        for(i = 0; i < 3; ++i)
        {
            glUniform1f(opacity_uniform, *p == ' ' || *p >= 'a' && *p <= '}' && !jiffies ? 0.0 : o);
            draw_frame(&char_anim, 524 + i * 77, 289, char_index(*p++));
        }

        glUniform1f(opacity_uniform, entry_opacity);
        draw_frame(&subtitle_anim, 0, 573, 3);
    }

    fade(&black_opacity, BLACK);
    fade(&intro_opacity, INTRO);
    fade(&highscore_opacity, HIGHSCORE);
    fade(&credits_opacity, CREDITS);
    fade(&title_opacity, TITLE);
    fade(&game_opacity, GAME);
    fade(&wood_opacity, WOOD);
    fade(&select_opacity, SELECT);
    fade(&house_opacity, HOUSE);
    fade(&fire_opacity, FIRE);
    fade(&entry_opacity, ENTRY);

    if(++jiffies > 4)
    {
        jiffies = 0;

        increment(&intro_anim);
        increment(&start_anim);

        if(intro_anim.frame == intro_anim.length - 1)
        {
            intro_anim.frame = 25;
            intro_anim.play = 0;
        }

        increment(&co2_anim);
        increment(&sun_anim);
        increment(&wat_anim);

        if((wood_anim.frame == 0 || wood_anim.play) && (
                level == 1 && wood_anim.frame == 5  ||
                level == 2 && wood_anim.frame == 5  ||
                level == 3 && wood_anim.frame == 10 ||
                level == 4 && wood_anim.frame == 15 ||
                level == 5 && wood_anim.frame == 20 ||
                level == 6 && wood_anim.frame == 25 ||
                0))
            wood_anim.play = 0;

        increment(&wood_anim);

        increment(&fire_anim);
        increment(&house_anim);
    }
}

#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<unistd.h>
#include<sys/time.h>
#include<math.h>
#include"./rand.h"


#define VERSION "1.2"
#define MAX_CONFIG_LINES 16
#define MAX_CONFIG_SIZE 2048
#define CONFIG_FILE "get_nfw_concentration.conf"
#define PROGNAME "get_nfw_concentration"

int count;

// Store data from configuration file

struct {
	float redshift;
	float a;
	float b;
	float min_mass;
	float max_mass;
	float sigma_logc;
	float delta;
} config[MAX_CONFIG_LINES];

void read_config(char* get_nfw_concentration_conf);
void help (void);
float c(float m, float redshift, long int start);
float p_logc(float logc, float mean_logc, float sigma_logc);
void usage(void);
void help(void);

int main(int argc, char *argv[])
{
	int s;
	float mass = 0.0;
	float redshift = 0.0;
	float delta = 200;
	long int seed = 0;
	
	while ((s = getopt(argc, argv, "m:z:d:s:h")) != -1) 
	{
		switch(s) {
			case 'm':
				mass=atof(optarg);
				break;
			case 'z':
				redshift=atof(optarg);
				break;
			case 'd':
 				delta=atof(optarg);
				break;
			case 's':
 				seed=atol(optarg);
				break;
			case 'h':
				help();
				exit(0);
			case '?':
				help();
				exit(1);
			default: 
				help();
				exit(0);
		}
	}

	if (mass==0.0) {
		fprintf(stderr, "%s error: at least -m option must be used.\n", PROGNAME);
		exit(1);
	}

	if (redshift < 0.0) {
		fprintf(stderr, "%s error: the redshift must be > 0.0\n", PROGNAME);
		exit(1);
	}

	read_config(CONFIG_FILE);
	
	fprintf(stdout, "%.2f\n",  c(mass, redshift, seed));

	return 0;
}

float c(float m, float z, long int start)
{
	int i;
	float u, v;
	float f, a, b;
	float logm, logc; // logc is the random variable
	long int seed;

	logm = log10(m);
	
	struct timeval tv;

	if (start > 0) {
		seed = start;
	} else {
		gettimeofday(&tv, NULL);
		seed = tv.tv_usec;
	//	printf( "%li \n", seed);
	}

	// verify redshift range
	if (z > config[count].redshift) {
		fprintf(stderr, "%s error: the redshift must be <= %.1f (max. value in %s)\n", PROGNAME, config[count].redshift, CONFIG_FILE);
		exit(1);
	}
		
	// select c(M,z) from configuration file
	for (i=count; i > 0; i--)
	{
		if (z >= config[i].redshift)
			break;
	}

	// Warning for mass range
	if ((logm > config[i].max_mass) || (logm < config[i].min_mass)) {
		fprintf(stderr, "%s warning: the mass must be between [%.3g-%.3g] Msol/h, verify the valid mass range for z=%.1f in %s.\n", PROGNAME, pow(10, config[i].min_mass), pow(10, config[i].max_mass), config[i].redshift, CONFIG_FILE);
		
	}
		
	// linear interpolation of z
	if (z == config[i].redshift) {
		f = 0;
	} else {
		f = (z - config[i].redshift)/(config[i+1].redshift - config[i].redshift);
	}

	a = config[i].a + f*(config[i+1].a - config[i].a);
	b = config[i].b + f*(config[i+1].b - config[i].b);

	// mean c(M) relation for a given z
	float mean_logc = a*logm + b;

	// scatter on logc at fixed mass is well represented by a normal pdf
	float sigma_logc = config[i].sigma_logc;
	
	// implements rejection method for a normal random generator
	float min_logc = mean_logc-3.0*sigma_logc;	
	float max_logc = mean_logc+3.0*sigma_logc;	
	float max_p_logc = p_logc(mean_logc, mean_logc, sigma_logc);

	do { 
		// sort a random point on logc vs. logM plane
		u=ran0((long)&seed);
		v=ran0((long)&seed);

		logc = min_logc+v*(max_logc-min_logc);

		// only accepts random points below the pdf
	} while ((u*max_p_logc) > (p_logc(logc, mean_logc, sigma_logc)));


	return pow(10.0, logc);

}

float p_logc(float logc, float mean_logc, float sigma_logc)
{ 
	// Probability density function for concentrations
	return 1.0/(sigma_logc*sqrt(2*M_PI))*exp(-0.5*(pow(((logc - mean_logc)/sigma_logc),2.0)));

}

void read_config(char* get_nfw_concentration_conf)
{
	char buffer[MAX_CONFIG_SIZE];
	char *p;
	FILE *fp;
	fp = fopen(get_nfw_concentration_conf, "r");

	if (!fp) {
		fprintf(stderr, "%s error: cannot open configuration file.\n", PROGNAME);
		exit(1);
	}
	memset(buffer,'\0',sizeof(buffer));
	fread(&buffer, sizeof(buffer), 1, fp);


	// remove comments from configuration file
	while (strchr(buffer,'#'))
		strcpy(buffer, strchr(buffer,'\n')+1);

	// printf("%s \n", buffer);

	count=-1;
	// # z  A  B MinMass MaxMass Sigma Delta 	
	do
	{
		count++;
		sscanf(buffer, "%f %f %f %f %f %f %f \n", &config[count].redshift, &config[count].a, &config[count].b, &config[count].min_mass, &config[count].max_mass, &config[count].sigma_logc, &config[count].delta);
		
		//printf("%f %f %f %f %f %f %f \n", config[count].redshift, config[count].a, config[count].b, config[count].min_mass, config[count].max_mass, config[count].sigma_logc, config[count].delta);

		p = strchr(buffer, '\n');
		if (p++) {
			strcpy(buffer, p);
		}
	} while ((strlen(buffer) > 0) && (count < MAX_CONFIG_LINES));	

	if (count < 1) {
		fprintf(stderr, "%s error: invalid configuration file.\n", PROGNAME);
		exit(1);
	}
		
}

void help(void)
{
	fprintf(stdout," get_nfw_concentration python module:\n\n First load the get_nfw_concentration configuration file:\n >>> get_nfw_concentration.read_config('get_nfw_concentration.conf')\n\n Then call:\n >>> get_nfw_concentration.c(mass, redshift, seed)\n to generate a random value of concentration for a given halo mass and redshift. \n Set seed as 0 for random generation based on the clock time, otherwise a fixed seed can be used to reproduce the same concentration value.\n");

}

void usage(void)
{
	fprintf(stderr,"Usage: get_nfw_concentration -m <mass> [-z <redshift>] [-d <over density>] [-s seed] [-h]\n\n\nget_nfw_concentration %s - Return the concentration parameter for a given halo mass and redshift. The input c(m,z) relations are specified in the configuration file 'get_nfw_concentration.conf'. \n\nOptions: \n\t-m : Set the halo mass in units of Msol/h\n\t-z : Set the halo redshift (default z=0) \n\t-d : Set the density constrast with respect to the critical density (Not implemented yet using by default Delta=200)\n\t-s : Fixed seed for random generator (default seed is variable, based on clock time)\n\t-h : Show this help\n\nNote: Mass and redshift values must lie in the range specified in the configuration file.\n", VERSION); 
}

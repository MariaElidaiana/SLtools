/** @file
* Example of doxygem documentation for C functions FIXME
*/

/** @package pseudo_elliptical_models
* Package to compute quantities related to Pseudo-Elliptical Models in the framework of Perturbative Approach
*
* Detailed description FIXME
*
*
*/
# ifndef PE_MODEL_H
# define PE_MODEL_H
#include <cmath> 

typedef double (*f_type2)   (double r, double pert_params[]); 

//!  First perturbative field for any Pseudo-Elliptical model as Perturbation.
//!
//!  \f$ \psi_E(r)=\phi_E(\xi)-\phi_0(r) \f$ 
//!
//!  \f$ \xi=r\sqrt{a_{1\eta}\cos^2{\theta}+a_{2\eta}\sin^2{\theta}}\f$ 
//!        (\f$ \xi_E\f$ is the elliptical variable \f$ \xi(r,\theta)\f$ for \f$ r=R_{E}\f$) 
//!
//!  \f$ f_{1}(\theta) := \left[\dfrac{\partial\psi_E(r,\theta)}{\partial r}\right]_{r=R_{E}}\f$
/*!
\param alpha_in : angle deflection of the circular potential
\param R_E: Einstein Radius
\param theta : angular coordinate in the lens plane,
 \param pert_params[] : PE lens parameters (pert_params[0] must be the ellipticity and pert_params[1] must be the flag choissing the parameterization)
\param iflag: flag control to choice the parameterization for the ellipticity (1,2,3) correspond to (G & K,Standard,Keeton's parameterizations)
  \return \f$ f_{1}(\theta) = \dfrac{\xi_{\mathrm{E}}}{R_{\mathrm{E}}}\alpha(\xi_{\mathrm{E}})-\alpha(R_{\mathrm{E}}) \f$
*/

double f1_pe(f_type2 alpha_in, double R_E, double theta, double pert_params[]){
double pot_params[]={pert_params[2],pert_params[3]};
double eps=pert_params[0], a_1eps,a_2eps;
int iflag=pert_params[1];

if(iflag==1){
// printf("You chose the Angle Deflection Parameterization");
a_1eps=1.-eps, a_2eps=1.+eps;
}

if(iflag==2){
// printf("You chose the standard parameterization");
a_1eps=1.-eps,a_2eps=1./a_1eps;
}

if(iflag==3){
// printf("You chose the Keeton's parameterization");
a_1eps=1.0, a_2eps=1./pow((1.-eps),2);
}

double xie=R_E*sqrt(a_1eps*pow(cos(theta),2)+a_2eps*pow(sin(theta),2));
double f1_tmp=(xie/R_E)*alpha_in(xie,pot_params)-alpha_in(R_E,pot_params);

return f1_tmp;
}

//!  Second perturbative field for any Pseudo-Elliptical as Perturbation (see PerturbedPNFW.pdf) 
//!
//!  \f$ \psi_E(r)=\phi_E(\xi)-\phi_0(r) \f$
//!
//!  \f$ \xi=r\sqrt{a_{1\eta}\cos^2{\theta}+a_{2\eta}\sin^2{\theta}}\f$
//!      (\f$ \xi_\mathrm{E}\f$ is the elliptical variable \f$ \xi(r,\theta)\f$ for \f$ r=R_{\mathrm{E}} \f$
//!
//!  \f$ \mathcal{G}(\eta)=R^2_{\mathrm{E}}\mathcal{A}(\eta)\sin{(2\theta)},\qquad \mathcal{A}=a_{2\eta}-a_{1\eta}\f$
//!
//!  \f$ \dfrac{df_0}{d\theta}:= \left[\dfrac{d \psi_E(r,\theta)}{d\theta}\right]_{r=R_{\mathrm{E}}} \f$
//!
/*!
  \param alpha_in : angle deflection for the circular model
  \param R_E: Einstein Radius corresponding to the circular model
  \param theta : angular coordinate in the lens plane
  \param pert_params[] : PNFW lens parameters, (pert_params[0] must be the ellipticity and pert_params[1] must be the flag choissing the parameterization)
  \param iflag: flag control to choice the parameterization for the ellipticity (1,2,3) correspond to (G & K,Standard,Keeton's parameterizations)
  \return \f$ \dfrac{df_0}{d\theta}= \frac{1}{2}\dfrac{\alpha(\xi_{\mathrm{E}})}{\xi_{\mathrm{E}}}\mathcal{G}(\eta,\theta) \f$ */

double df0dtheta_pe(f_type2 alpha_in,double R_E, double theta, double pert_params[]){
double pot_params[]={pert_params[2],pert_params[3]};
double eps=pert_params[0], a_1eps,a_2eps;
int iflag=pert_params[1];

if(iflag==1){
// printf("You chose the Angle Deflection Parameterization");
a_1eps=1.-eps, a_2eps=1.+eps;
}

if(iflag==2){
// printf("You chose the standard parameterization");
a_1eps=1.-eps,a_2eps=1./a_1eps;
}

if(iflag==3){
// printf("You chose the Keeton's parameterization");
a_1eps=1.0, a_2eps=1./pow((1.-eps),2);
}

double script_A=a_2eps-a_1eps;
double xie=R_E*sqrt(a_1eps*pow(cos(theta),2)+a_2eps*pow(sin(theta),2));
double cal_G = pow(R_E,2)*script_A*sin(2*theta);
double df0dte_pe=0.5*(alpha_in(xie,pot_params)/xie)*cal_G;

return df0dte_pe;

}

//!  Solution for  any Pseudo-Elliptical as perturbation,useful for critical and caustic lines
//!
//!  \f$ \psi_E(r)=\phi_E(\xi)-\phi_0(r) \f$
//!
//!  \f$ \xi=r\sqrt{a_{1\eta}\cos^2{\theta}+a_{2\eta}\sin^2{\theta}}\f$
//!                  (\f$ \xi_\mathrm{E}\f$ is the elliptical variable \f$ \xi(r,\theta)\f$ for \f$ r=R_{\mathrm{E}})\f$ 
//!
//! \f$ \dfrac{d^2f_0}{d\te^2}=\frac{1}{2}\mathcal{G}_\te(\eta,\theta)\dfrac{\alpha(\xi_{\mathrm{E}})}{\xi_{\mathrm{E}}}-\frac{\gamma(\xi_{\mathrm{E}})}{2}\left[ \dfrac{\mathcal{G}(\eta,\theta)}{\xi_{\mathrm{E}}}\right]^2 \f$
//! 
//!  \f$ \mathcal{G}(\eta)=R^2_{\mathrm{E}}\mathcal{A}(\eta)\sin{(2\theta)},\qquad \mathcal{A}=a_{2\eta}-a_{1\eta}\f$
//!
//!  \f$ \mathcal{G}_{\theta}(\eta)= 2\,R^2_{\mathrm{E}}\mathcal{A}(\eta)\cos{(2\theta)}\f$
//!
//! \f$ \gamma(\xi_{\mathrm{E}})=\kappa(\xi_{\mathrm{E}})-\dfrac{\alpha(\xi_{\mathrm{E}})}{\xi_{\mathrm{E}}} \f$
/*!
  \param alpha_in : angle deflection of the circular potential
  \param gamma_in : shear of the circular potential
  \param R_E: Einstein Radius of the circular potential
  \param theta : angular coordinate in the lens plane
  \param pert_params[] : PNFW lens parameters, (pert_params[0] must be the ellipticity and pert_params[1] must be the flag choissing the parameterization)
  \param iflag: flag control to choice the parameterization for the ellipticity (1,2,3) correspond to (G & K,Standard,Keeton's parameterizations)
  \return \f$ \dfrac{d^2f_0}{d\theta^2}\f$
*/

double d2f0dtheta2_pe(f_type2 alpha_in,f_type2 shear_in, double R_E, double theta, double pert_params[]){
double pot_params[]={pert_params[2],pert_params[3]};
double eps=pert_params[0], a_1eps,a_2eps;
int iflag=pert_params[1];

if(iflag==1){
// printf("You chose the Angle Deflection Parameterization");
a_1eps=1.-eps, a_2eps=1.+eps;
}

if(iflag==2){
// printf("You chose the standard parameterization");
a_1eps=1.-eps,a_2eps=1./a_1eps;
}

if(iflag==3){
// printf("You chose the Keeton's parameterization");
a_1eps=1.0, a_2eps=1./pow((1.-eps),2);
}

double script_A=a_2eps-a_1eps;
double xie=R_E*sqrt(a_1eps*pow(cos(theta),2)+a_2eps*pow(sin(theta),2));
double cal_G = pow(R_E,2)*script_A*sin(2*theta);
double cal_gsq=pow((cal_G/xie),2);
double dcal_G=2.*pow(R_E,2)*script_A*cos(2*theta);

double d2f0dte2_aux=0.5*dcal_G*(alpha_in(xie,pot_params)/xie)-0.5*shear_in(xie,pot_params)*cal_gsq;
return d2f0dte2_aux;
}

#endif
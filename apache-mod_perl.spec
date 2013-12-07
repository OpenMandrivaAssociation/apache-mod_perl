#(ie. use with rpm --rebuild):
#
#	--with debug	Compile with debugging code
# 
#  enable build with debugging code: will _not_ strip away any debugging code,
#  will _add_ -g3 to CFLAGS, will _add_ --enable-maintainer-mode to 
#  configure.

%define build_debug 0
%define build_test 0

%define svn_rev 1458708

# commandline overrides:
# rpm -ba|--rebuild --with 'xxx'
%{?_with_debug: %{expand: %%global build_debug 1}}
%{?_without_debug: %{expand: %%global build_debug 0}}
%{?_with_test: %{expand: %%global build_test 1}}
%{?_without_test: %{expand: %%global build_test 0}}

%if %{build_debug}
# disable build root strip policy
%define __spec_install_post %{_libdir}/rpm/brp-compress || :

# This gives extra debuggin and huge binaries
%{expand:%%define optflags %{optflags} %([ ! $DEBUG ] && echo '-g3')}
%endif

%if %{build_debug}
%define build_test 1
%define build_debug 1
%endif

#Module-Specific definitions
%define apache_version 2.4.0
%define mod_name mod_perl
%define load_order 175
%define perl_version %(rpm -q --qf '%%{epoch}:%%{version}' perl)

Summary:	An embedded Perl interpreter for the apache Web server
Name:		apache-%{mod_name}
Version:	2.0.7
%if %{svn_rev}
Release:	2.svn%{svn_rev}.2
%else
Release:	7
%endif
Group:		System/Servers
License:	Apache License
URL:		http://perl.apache.org/
%if %{svn_rev}
Source0:        %{mod_name}-%{version}-svn%{svn_rev}.tar.gz
%else
Source0:	http://perl.apache.org/dist/%{mod_name}-%{version}.tar.gz
Source1:	http://perl.apache.org/dist/%{mod_name}-%{version}.tar.gz.asc
%endif
Source2:	mod_perl.conf
Source3:	apache-mod_perl-testscript.pl
Patch0:		mod_perl-2.0.4-inline.patch
Requires:       perl = %{perl_version}
BuildRequires:	perl-devel >= 5.8.2
BuildRequires:  perl-Tie-IxHash
BuildRequires:	perl-Data-Flow
BuildRequires:  apache-mpm-prefork
%if %{build_test}
BuildRequires:	perl-CGI >= 1:3.08
BuildRequires:	perl-HTML-Parser
BuildRequires:	perl-libwww-perl
BuildRequires:	perl-URI
BuildRequires:	perl-BSD-Resource
BuildRequires:	apache-mpm-prefork >= %{apache_version}
BuildRequires:	apache-base >= %{apache_version}
BuildRequires:	apache-modules >= %{apache_version}
BuildRequires:	apache-mod_cache >= %{apache_version}
BuildRequires:	apache-mod_dav >= %{apache_version}
BuildRequires:	apache-mod_deflate >= %{apache_version}
BuildRequires:	apache-mod_disk_cache >= %{apache_version}
BuildRequires:	apache-mod_file_cache >= %{apache_version}
BuildRequires:	apache-mod_ldap >= %{apache_version}
BuildRequires:	apache-mod_proxy >= %{apache_version}
BuildRequires:	apache-mod_ssl >= %{apache_version}
BuildRequires:	apache-mod_suexec >= %{apache_version}
BuildRequires:	apache-mod_userdir >= %{apache_version}
%endif
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):  apache-mpm-prefork >= %{apache_version}
Requires(pre):  apache-base >= %{apache_version}
Requires(pre):  apache-modules >= %{apache_version}
Requires:	apache-mpm-prefork >= %{apache_version}
Requires:	apache-base >= %{apache_version}
Requires:	apache-modules >= %{apache_version}
Requires:	perl(Apache2::Reload)
BuildRequires:	apache-devel >= %{apache_version}
Obsoletes:	perl-Apache-Reload
Epoch:		1

%description
%{name} incorporates a Perl interpreter into the apache web server,
so that the Apache web server can directly execute Perl code.
Mod_perl links the Perl runtime library into the apache web server and
provides an object-oriented Perl interface for apache's C language
API.  The end result is a quicker CGI script turnaround process, since
no external Perl interpreter has to be started.

Install %{name} if you're installing the apache web server and you'd
like for it to directly incorporate a Perl interpreter.

You can build %{name} with some conditional build swithes;

(ie. use with rpm --rebuild):
    --with[out] debug	Compile with debugging code (forces --with test)
    --with[out]	test	Initiate a Apache-Test run

%package	devel
Summary:	Files needed for building XS modules that use mod_perl
Group:		Development/C
Requires:	%{name} = 1:%{version}
Requires:	apache-devel >= %{apache_version}
Epoch:		1

%description	devel 
The mod_perl-devel package contains the files needed for building XS
modules that use mod_perl.

%prep

%if %{svn_rev}
%setup -q -n %{mod_name}-%{version}-svn%{svn_rev}
%else
%setup -q -n %{mod_name}-%{version}
%endif

%patch0 -p1 -b .inline

cp %{SOURCE2} .
perl -pi -e "s|_MODULE_DIR_|%{_libdir}/apache|g" mod_perl.conf

for i in `find . -type d -name .svn`; do
    if [ -e "$i" ]; then rm -rf $i; fi >&/dev/null
done

%build

# Compile the module.

#%{__perl} Makefile.PL \
#    MP_APXS=%{_bindir}/apxs \
#    MP_APR_CONFIG=%{_bindir}/apr-1-config
#
#make source_scan
#make xs_generate

%{__perl} Makefile.PL \
%if %{build_debug}
    MP_MAINTAINER=1 \
    MP_TRACE=1 \
    MP_CCOPTS="$(%{_bindir}/apxs -q CFLAGS|sed -e 's/-fPIE//') -g3 -Werror -fPIC" \
%else
    MP_CCOPTS="$(%{_bindir}/apxs -q CFLAGS|sed -e 's/-fPIE//') -fPIC" \
%endif
    MP_APXS=%{_bindir}/apxs \
    MP_APR_CONFIG=%{_bindir}/apr-1-config \
    INSTALLDIRS=vendor </dev/null 

ln -s Apache-mod_perl_guide-1.29/bin bin
%make

# XXX mod_include/SSI does not include files when they are not named .shtml
mv t/htdocs/includes-registry/test.pl t/htdocs/includes-registry/test.shtml
mv t/htdocs/includes-registry/cgipm.pl t/htdocs/includes-registry/cgipm.shtml
sed 's/\.pl/.shtml/' t/htdocs/includes/test.shtml > tmpfile && mv tmpfile t/htdocs/includes/test.shtml

%install

%if %{build_debug}
export DONT_STRIP=1
%endif

%if %{build_test}
# Run the test suite.
#  Need to make t/htdocs/perlio because it isn't expecting to be run as
#  root and will fail tests that try and write files because the server
#  will have changed it's uid.
mkdir -p t/htdocs/perlio
chmod 777 t/htdocs/perlio

#
# fix for bad_scripts.t in 1.99_12
# [Tue Mar 02 17:28:26 2004] [error] file permissions deny server execution/usr/src/packages/BUILD/modperl-2.0/ModPerl-Registry/t/cgi-bin/r_inherited.pl
if test -e ModPerl-Registry/t/cgi-bin/r_inherited.pl; then chmod +x ModPerl-Registry/t/cgi-bin/r_inherited.pl; fi
#
# 1.99_12_20040302 fix for t/hooks/cleanup.t and t/hooks/cleanup2.t
# [Tue Mar 02 18:38:41 2004] [error] [client 127.0.0.1] can't open /usr/src/packages/BUILD/modperl-2.0/t/htdocs/hooks/cleanup2: Permission denied at /usr/src/packages/BUILD/modperl-2.0/Apache-Test/lib/Apache/TestUtil.pm line 82.
mkdir -p t/htdocs/hooks
chmod 2770 t/htdocs/hooks
#
# run test suite:
#
#make TEST_VERBOSE=1 APACHE_TEST_PORT=select APACHE_TEST_STARTUP_TIMEOUT=360 test  || {
#       ps aufx | grep "/usr/sbin/httpd-prefork -d /usr/src/packages/BUILD/modperl-2.0" \
#               | grep -v grep | awk '{print $2}' | xargs -r kill
#       exit 1
#}
perl t/TEST -start-httpd -port select -startup_timeout 360 -verbose -httpd_conf /etc/httpd/conf/httpd.conf
perl t/TEST -run-tests || {
perl t/TEST -stop-httpd
    exit 1
}
perl t/TEST -stop-httpd
# in case of failures, see http://perl.apache.org/docs/2.0/user/help/help.html#_C_make_test___Failures
# then, debug like this:
# t/TEST -start-httpd
# tail -F t/logs/*&
# t/TEST -run-tests -verbose $failed_test
# t/TEST -stop-httpd

#make \
#    APACHE_TEST_PORT=select \
#    APACHE_TEST_STARTUP_TIMEOUT=30 \
#    APACHE_TEST_COLOR=1 \
#    TEST_VERBOSE=1 \
#    APACHE_TEST_HTTPD=%{_sbindir}/httpd \
#    APACHE_TEST_APXS=%{_sbindir}/apxs \
#    test

%endif

# make some directories
install -d %{buildroot}%{_libdir}/apache
install -d %{buildroot}%{_sysconfdir}/httpd/modules.d
install -d %{buildroot}%{_var}/www/perl

%makeinstall_std \
    MODPERL_AP_LIBEXECDIR=%{_libdir}/apache \
    MODPERL_AP_INCLUDEDIR=%{_includedir}/apache \
    INSTALLDIRS=vendor

install -m0644 mod_perl.conf %{buildroot}%{_sysconfdir}/httpd/modules.d/%{load_order}_%{mod_name}.conf

# Remove empty file
rm -f docs/api/mod_perl-2.0/pm_to_blib

install -m0755 %{SOURCE3} %{buildroot}%{_var}/www/perl

# install missing required files
install -d %{buildroot}%{perl_vendorarch}/Apache2/Apache
install -m0644 xs/tables/current/Apache2/ConstantsTable.pm %{buildroot}%{perl_vendorarch}/Apache2/Apache/
install -m0644 xs/tables/current/Apache2/FunctionTable.pm %{buildroot}%{perl_vendorarch}/Apache2/Apache/
install -m0644 xs/tables/current/Apache2/StructureTable.pm %{buildroot}%{perl_vendorarch}/Apache2/Apache/

# cleanup
find %{buildroot}%{perl_archlib} -name perllocal.pod | xargs rm -f

# don't pack the Apache-Test stuff
rm -f %{buildroot}%{perl_vendorarch}/Apache/Test*
rm -rf %{buildroot}%{perl_vendorarch}/MyTest*
rm -f %{buildroot}%{perl_vendorarch}/Bundle/ApacheTest.pm
rm -f %{buildroot}%{_mandir}/man3/Apache::Test*
rm -f %{buildroot}%{_mandir}/man3/Bundle::ApacheTest.3pm

# do not ship the patch backups
find %{buildroot}%{perl_vendorarch} -name '*.pm.cve*' | xargs rm -f

%post
/bin/systemctl daemon-reload >/dev/null 2>&1 || :

%postun
if [ "$1" = "0" ]; then
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%files -n %{name}
%doc Changes INSTALL LICENSE README docs todo
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/*.conf
%attr(0755,root,root) %{_libdir}/apache/*.so
%{perl_vendorarch}/Apache
%{perl_vendorarch}/Apache2
%{perl_vendorarch}/Bundle
%{perl_vendorarch}/ModPerl
%{perl_vendorarch}/APR
%{perl_vendorarch}/APR.pm
%{perl_vendorarch}/mod_perl2.pm
%{perl_vendorarch}/auto/Apache2/FilterRec
%{perl_vendorarch}/auto/Apache2/Util
%{perl_vendorarch}/auto/Apache2/RequestRec
%{perl_vendorarch}/auto/Apache2/Command
%{perl_vendorarch}/auto/Apache2/ConnectionUtil
%{perl_vendorarch}/auto/Apache2/Module
%{perl_vendorarch}/auto/Apache2/typemap
%{perl_vendorarch}/auto/Apache2/URI
%{perl_vendorarch}/auto/Apache2/Process
%{perl_vendorarch}/auto/Apache2/MPM
%{perl_vendorarch}/auto/Apache2/Response
%{perl_vendorarch}/auto/Apache2/SubProcess
%{perl_vendorarch}/auto/Apache2/Build
%{perl_vendorarch}/auto/Apache2/Const
%{perl_vendorarch}/auto/Apache2/Filter
%{perl_vendorarch}/auto/Apache2/Log
%{perl_vendorarch}/auto/Apache2/ServerUtil
%{perl_vendorarch}/auto/Apache2/ServerRec
%{perl_vendorarch}/auto/Apache2/CmdParms
%{perl_vendorarch}/auto/Apache2/Provider
%{perl_vendorarch}/auto/Apache2/RequestUtil
%{perl_vendorarch}/auto/Apache2/RequestIO
%{perl_vendorarch}/auto/Apache2/SubRequest
%{perl_vendorarch}/auto/Apache2/Directive
%{perl_vendorarch}/auto/Apache2/HookRun
%{perl_vendorarch}/auto/Apache2/Access
%{perl_vendorarch}/auto/Apache2/Connection
%{perl_vendorarch}/auto/ModPerl/Util
%{perl_vendorarch}/auto/ModPerl/Global
%{perl_vendorarch}/auto/ModPerl/Const
%{perl_vendorarch}/auto/APR/BucketAlloc
%{perl_vendorarch}/auto/APR/IpSubnet
%{perl_vendorarch}/auto/APR/Util
%{perl_vendorarch}/auto/APR/Pool
%{perl_vendorarch}/auto/APR/Finfo
%{perl_vendorarch}/auto/APR/Socket
%{perl_vendorarch}/auto/APR/Brigade
%{perl_vendorarch}/auto/APR/URI
%{perl_vendorarch}/auto/APR/Error
%{perl_vendorarch}/auto/APR/ThreadRWLock
%{perl_vendorarch}/auto/APR/Bucket
%{perl_vendorarch}/auto/APR/Const
%{perl_vendorarch}/auto/APR/APR.so
%{perl_vendorarch}/auto/APR/Status
%{perl_vendorarch}/auto/APR/SockAddr
%{perl_vendorarch}/auto/APR/String
%{perl_vendorarch}/auto/APR/OS
%{perl_vendorarch}/auto/APR/PerlIO
%{perl_vendorarch}/auto/APR/ThreadMutex
%{perl_vendorarch}/auto/APR/Date
%{perl_vendorarch}/auto/APR/UUID
%{perl_vendorarch}/auto/APR/BucketType
%{perl_vendorarch}/auto/APR/Base64
%{perl_vendorarch}/auto/APR/Table

%{_mandir}/*/*
%attr(0755,root,root) %{_var}/www/perl/*.pl

%files devel
%attr(0755,root,root) %{_bindir}/*
%{_includedir}/apache/*


%changelog
* Wed Jun 06 2012 Bernhard Rosenkraenzer <bero@bero.eu> 1:2.0.7-1
+ Revision: 802969
- 2.0.7
- Fix compatibility with httpd 2.4.x

* Thu May 31 2012 Crispin Boylan <crisb@mandriva.org> 1:2.0.6-5
+ Revision: 801503
+ rebuild (emptylog)

* Wed May 16 2012 Crispin Boylan <crisb@mandriva.org> 1:2.0.6-4
+ Revision: 799117
- Fix Apache2::MPM requires again

* Tue May 15 2012 Crispin Boylan <crisb@mandriva.org> 1:2.0.6-3
+ Revision: 799059
- Dont remove SizeLimit stuff
- Add requires exception on Apache::SizeLimit

* Tue May 15 2012 Crispin Boylan <crisb@mandriva.org> 1:2.0.6-2
+ Revision: 798997
- Use provided Apache-Test to avoid circular dependency
- Add apache2::MPM to requires exceptions

* Mon May 14 2012 Crispin Boylan <crisb@mandriva.org> 1:2.0.6-1
+ Revision: 798815
- Patch2: httpd2.4 fix from fedora
- Drop patch2 (merged upstream)
- New release
- Rebuild

  + Oden Eriksson <oeriksson@mandriva.com>
    - fix build (though it needs a new upcoming version...)
    - simplify the configuration a bit

* Wed Feb 08 2012 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.5-4
+ Revision: 771924
- rebuild

* Fri Jan 27 2012 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.5-3
+ Revision: 769314
- filter out -fPIE

  + Per Øyvind Karlsen <peroyvind@mandriva.org>
    - mass rebuild of perl extensions against perl 5.14.2

* Thu May 12 2011 Guillaume Rousse <guillomovitch@mandriva.org> 1:2.0.5-2
+ Revision: 673877
- obsoletes perl-Apache-Reload, as its content has been merged

* Mon May 09 2011 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.5-1
+ Revision: 672996
- 2.0.5
- drop the CVE-2009-0796 fix, it's in there
- adjust the format string patch a bit

* Mon Apr 11 2011 Funda Wang <fwang@mandriva.org> 1:2.0.4-21
+ Revision: 652458
- rebuild

* Sat Feb 12 2011 Guillaume Rousse <guillomovitch@mandriva.org> 1:2.0.4-20
+ Revision: 637363
- rebuild for latest perl

* Thu Dec 02 2010 Paulo Andrade <pcpa@mandriva.com.br> 1:2.0.4-19mdv2011.0
+ Revision: 605047
- Rebuild with apr with workaround to issue with gcc type based alias analysis

* Sun Oct 24 2010 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-18mdv2011.0
+ Revision: 588283
- rebuild

* Wed Sep 08 2010 Jérôme Quelin <jquelin@mandriva.org> 1:2.0.4-17mdv2011.0
+ Revision: 576756
- rebuild for perl 5.12.2

* Tue Jul 27 2010 Funda Wang <fwang@mandriva.org> 1:2.0.4-16mdv2011.0
+ Revision: 562062
- rebuild
- rebuild

* Tue Jul 20 2010 Sandro Cazzaniga <kharec@mandriva.org> 1:2.0.4-14mdv2011.0
+ Revision: 555414
- rebuild

* Mon Mar 08 2010 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-13mdv2010.1
+ Revision: 515838
- rebuilt for apache-2.2.15

* Fri Jan 01 2010 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-12mdv2010.1
+ Revision: 484731
- rebuilt against bdb 4.8

* Wed Sep 30 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-11mdv2010.0
+ Revision: 451701
- rebuild

* Tue Aug 25 2009 Jérôme Quelin <jquelin@mandriva.org> 1:2.0.4-10mdv2010.0
+ Revision: 420947
- rebuild

* Thu Aug 13 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-9mdv2010.0
+ Revision: 416011
- add requires on perl(Apache2::Reload) as it was broken out but needed

* Fri Jul 31 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-8mdv2010.0
+ Revision: 405139
- rebuild

* Wed Jun 10 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-7mdv2010.0
+ Revision: 384877
- rebuild one more time...
- rebuilt against new apr/apr-util libs

* Sun Apr 12 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-5mdv2009.1
+ Revision: 366464
- P3: security fix for CVE-2009-0796

* Mon Mar 23 2009 Anssi Hannula <anssi@mandriva.org> 1:2.0.4-4mdv2009.1
+ Revision: 360706
- fix format strings for -Wformat-security (format-string.patch)

  + Oden Eriksson <oeriksson@mandriva.com>
    - sync with fedora

* Mon Dec 15 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-3mdv2009.1
+ Revision: 314521
- rebuilt against db4.7

* Mon Jul 14 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-2mdv2009.0
+ Revision: 235642
- rebuild

* Thu Jun 05 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-1mdv2009.0
+ Revision: 215292
- rebuild

* Sun May 04 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-0.1mdv2009.0
+ Revision: 200953
- 2.0.4

* Fri Mar 07 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-0.r634243.2mdv2008.1
+ Revision: 181440
- rebuild

* Thu Mar 06 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-0.r634243.1mdv2008.1
+ Revision: 180857
- new snap (r634243)

* Tue Feb 12 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-0.r620824.1mdv2008.1
+ Revision: 166150
- new svn snap (620824)
- rpmlint fixes

* Tue Jan 15 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.4-0.r612173.1mdv2008.1
+ Revision: 153063
- 2.0.4-dev use a recent svn snap (r612173)
- drop upstream implemented P1 (CVE-2007-1349)
- removed one hunk from P0

  + Thierry Vignaud <tv@mandriva.org>
    - rebuild
    - rebuild

* Fri Dec 21 2007 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.3-9mdv2008.1
+ Revision: 136532
- rebuilt against new build deps

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Tue Nov 20 2007 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.3-8mdv2008.1
+ Revision: 110774
- rebuild
- better error 403 message

* Sat Sep 08 2007 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.3-7mdv2008.0
+ Revision: 82362
- rebuild

* Thu Aug 16 2007 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.3-6mdv2008.0
+ Revision: 64322
- use the new %%serverbuild macro

* Wed Jun 13 2007 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.3-5mdv2008.0
+ Revision: 38414
- rebuild

* Thu Apr 19 2007 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.3-4mdv2008.0
+ Revision: 14937
- P1: security fix for CVE-2007-1349
- remove the .pm patch backups before final packaging


* Sat Mar 10 2007 Oden Eriksson <oeriksson@mandriva.com> 2.0.3-3mdv2007.1
+ Revision: 140585
- rebuild

* Tue Feb 27 2007 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.3-2mdv2007.1
+ Revision: 126617
- general cleanups

* Tue Dec 12 2006 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.3-1mdv2007.1
+ Revision: 95876
- 2.0.3
- bunzipped the config file
- fix deps
- rediffed P0

* Tue Dec 12 2006 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.2-9mdv2007.1
+ Revision: 95734
- rebuild
- Import apache-mod_perl

* Tue Jun 20 2006 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-8mdv2007.0
- drop the broken DESTDIR patch

* Mon Jan 23 2006 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-7mdk
- rebuilt against perl-5.8.8-0.RC1.1mdk
- added one small DESTDIR patch and use %%makeinstall_std instead

* Tue Jan 03 2006 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-6mdk
- oops!, really delete the bundled Apache-Test

* Tue Jan 03 2006 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-5mdk
- fix deps

* Tue Dec 13 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-4mdk
- fix the config

* Mon Dec 12 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-3mdk
- rebuilt against apache-2.2.0

* Sun Oct 30 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-2mdk
- rebuilt to provide a -debug package too

* Sun Oct 30 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-1mdk
- 2.0.2
- rediffed P0

* Wed Oct 19 2005 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.1-2mdk
- fix deps

* Mon Oct 17 2005 Oden Eriksson <oeriksson@mandriva.com> 1:2.0.1-6mdk
- rebuilt for apache-2.0.55
- fix versioning

* Tue Sep 06 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.1-6mdk
- rebuild

* Wed Aug 31 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.1-5mdk
- rebuilt against new openldap-2.3.6 libs

* Thu Aug 11 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.1-4mdk
- fix deps

* Sat Jul 30 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.1-3mdk
- added another work around for a rpm bug

* Sat Jul 30 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.1-2mdk
- added a work around for a rpm bug, "Requires(foo,bar)" don't work

* Thu Jul 07 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.1-1mdk
- 2.0.1

* Mon Jun 20 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.0-4mdk
- nuke the bundled Apache-Test and use the "system" one
- reworked the --with/--without spec file magic
- fix deps

* Fri Jun 10 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.0-3mdk
- fix deps

* Sun Jun 05 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.0-2mdk
- run the test suite

* Sat May 28 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.0-1mdk
- 2.0.0 final
- fix #12874 and #15586

* Fri May 20 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.0-0.RC6.1mdk
- 2.0.0 RC6
- the apache-mod_perl-startup.pl file seems not needed anymore, so don't use it
- the conf.d directory is renamed to modules.d
- use new rpm-4.4.x pre,post magic

* Wed Apr 20 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.0-0.RC5.1mdk
- 2.0.0 RC5
- renamed to apache-mod_perl
- nuke rpath

* Thu Mar 17 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0.0-0.RC4.6mdk
- use the %%mkrel macro

* Sun Feb 27 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0.0-0.RC4.5mdk
- fix %%post and %%postun to prevent double restarts

* Wed Feb 16 2005 Stefan van der Eijk <stefan@eijk.nu> 2.0.53_2.0.0-0.RC4.4mdk
- fix bug #6574

* Wed Feb 16 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0.0-0.RC4.3mdk
- fix deps

* Tue Feb 15 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0.0-0.RC4.2mdk
- spec file cleanups, remove the ADVX-build stuff

* Tue Feb 08 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0.0-0.RC4.1mdk
- rebuilt for apache 2.0.53

* Tue Feb 08 2005 Buchan Milne <bgmilne@linux-mandrake.com> 2.0.52_2.0.0-0.RC4.6mdk
- rebuild for ldap2.2_7

* Sun Feb 06 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC4.5mdk
- fix deps

* Sun Feb 06 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC4.4mdk
- fix deps

* Sat Feb 05 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC4.3mdk
- rebuilt against new openldap libs

* Mon Jan 31 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC4.2mdk
- added conditional build deps if a "--with test" build
- fix requires-on-release

* Sat Jan 22 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC4.1mdk
- mod_perl-2.0.0-RC4
- drop upstream P0
- the tests nearly passes now, 6/222 fails, not bad... thanks to Stas Bekman
  for the "-httpd_conf /etc/httpd/conf/httpd2.conf" tip

* Fri Jan 21 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC3.5mdk
- drop bogus deps

* Fri Jan 14 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC3.4mdk
- try and make the make test work, used stuff from fedora and suse
- don't pack the bundled Apache-Test stuff
- use less restrictive permissions on the config files

* Wed Jan 12 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC3.3mdk
- drop the fake Apache::Status stuff from the testscript.pl file
- fix deps

* Tue Jan 11 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC3.2mdk
- make --with debug work

* Mon Jan 10 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0.0-0.RC3.1mdk
- mod_perl-2.0.0-RC3
- nuke fake Apache::Status as this is included and works now
- make test just bombs out (it thinks we are apache1)..., disable it for now

* Tue Nov 30 2004 Rafael Garcia-Suarez <rgarciasuarez@mandrakesoft.com> 2.0.52_1.99_17-6mdk
- really rebuilt against perl-5.8.6

* Tue Nov 30 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_1.99_17-5mdk
- rebuilt against perl-5.8.6

* Tue Nov 16 2004 Michael Scherer <misc@mandrake.org> 2.0.52_1.99_17-4mdk
- Rebuild for new perl

* Tue Nov 09 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_1.99_17-3mdk
- rebuild against newish apr libs

* Tue Nov 09 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_1.99_17-2mdk
- rule out some more perl* stuff (fedora)
- fix deps

* Sun Oct 24 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.99_17-1mdk
- 1.99_17

* Wed Sep 29 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_1.99_16-1mdk
- built for apache 2.0.52

* Fri Sep 17 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.51_1.99_16-1mdk
- built for apache 2.0.51

* Wed Aug 25 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.99_16-1mdk
- 1.99_16

* Sun Aug 22 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.99_15-1mdk
- 1.99_15
- fixed S6

* Wed Aug 11 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.99_14-5mdk
- rebuilt

* Wed Jul 14 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.99_14-4mdk
- rule out perl(Carp::Heavy) as perl in mdk10.0 doesn't seem to provide
  it (though it has since 5.6.1)

* Tue Jul 13 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.99_14-3mdk
- remove redundant provides

* Fri Jul 09 2004 Rafael Garcia-Suarez <rgarciasuarez@mandrakesoft.com> 2.0.50_1.99_14-2mdk
- Rebuild for new perl

* Thu Jul 01 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.99_14-1mdk
- built for apache 2.0.50

* Tue Jun 22 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.49_1.99_14-3mdk
- fix conflicting man page with mod_perl-common-1.3.31_1.29-1mdk

* Wed Jun 16 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.49_1.99_14-2mdk
- fix license
- rule out Data::Flow as it's not needed (rgarciasuarez@mandrakesoft.com)

* Sat Jun 12 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.49_1.99_14-1mdk
- 1.99_14
- built for apache 2.0.49

* Wed Apr 07 2004 Michael Scherer <misc@mandrake.org> 2.0.48_1.99_11-4mdk 
- rebuild for new perl
- remove parallel compilation


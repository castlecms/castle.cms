from plone.app.textfield import RichTextValue


def getTileData():
    TOP_FULL_WIDTH = u"""
        <div class="text-center">
            <blockquote>CastleCMS powers websites, intranets, and web applications for the most demanding organizations. Built on top of&nbsp;Plone, the&nbsp;dependable open source content management system (CMS), CastleCMS provides a unique combination of world-class&nbsp;content management features and maximum&nbsp;security, and is the result of our team's years of experience leading&nbsp;Plone development&nbsp;and&nbsp;security.</blockquote>
        </div>"""  # noqa

    THREE_WIDE_1 = u"""
                    <h4 class="text-center">Collaborate Effectively</h4>
                    <p>CastleCMS was built for large team collaboration. Fine-grained security for group editing and viewing,&nbsp;versioning, tagging, and content quality checks: all the features&nbsp;you need to create and manage content worthy of any enterprise.</p>
                    """  # noqa

    THREE_WIDE_2 = u"""
                    <h4 class="text-center">Theming, Your Way</h4>
                    <p>Create and modify&nbsp;your website theme live, using&nbsp;only a web browser, with the freedom to customize all aspects of CastleCMS. Apply your corporate brand&nbsp;exactly as you envisioned, with the most powerful and flexible theming engine available.</p>
                    """  # noqa

    THREE_WIDE_3 = u"""
                    <h4 class="text-center">Social Media Integration</h4>
                    <p>Engage your users, customers and audience more effectively than ever before, using CastleCMS' built-in&nbsp;social media platform integrations: Facebook, Twitter, Pinterest, Instagram, Google Plus, YouTube, AddThis, Disqus, GitHub, and more.</p>
                    """  # noqa

    TRY_CASTLE = u"""
                    <h2 style="text-align: center;">TRY CASTLECMS</h2>
                    <div class="row text-center">
                        <div class="col-xs-10 col-xs-offset-1 col-md-4 col-md-offset-1 col-lg-3 col-lg-offset-2">
                            <h4>Sign up for a free demo today, and see how CastleCMS can benefit your business.</h4>
                            <a data-val="410ec18805c44056813340350594a777" data-mce-href="resolveuid/410ec18805c44056813340350594a777" data-linktype="internal" href="https://castlecms.io/contact" class="btn btn-ghost" data-urltype="_direct_">Book a Demo</a>
                        </div>
                        <div class="col-md-2" style="margin: 20px 0;" data-mce-style="margin: 20px 0;">&nbsp;<img data-scale="mini" src="/++theme++castle.theme/img/frontpage/demo-icons.png" alt="Demo"></div><div class="col-xs-10 col-xs-offset-1 col-md-4 col-md-offset-0 col-lg-3">
                            <h4>Just looking for a quote? <br>Call <a href="tel:+17158693440" data-mce-href="tel:+17158693440">(715) 869-3440</a>, email <a href="mailto:info@wildcardcorp.com" data-mce-href="mailto:info@wildcardcorp.com">info@wildcardcorp.com</a>, or fill out <a data-val="410ec18805c44056813340350594a777" title="Demo and Quote Request" data-linktype="internal" href="https://castlecms.io/contact" data-mce-href="resolveuid/410ec18805c44056813340350594a777" data-urltype="_direct_">our form</a>.</h4>
                        </div>
                    </div>
                    """  # noqa

    TWO_WIDE_1_1 = u"""
                    <h4>What technology is CastleCMS built on?</h4>
                    <p>The core of CastleCMS comes from <a title="Plone, the ultimate open source enterprise content management system" href="https://plone.com" target="_blank" data-linktype="external" data-urltype="/view" data-val="https://plone.com" data-mce-href="https://plone.com">Plone</a>, the open source CMS&nbsp;with <a title="Plone, the high security open source content management system" href="https://plone.com/secure" target="_blank" data-linktype="external" data-urltype="/view" data-val="https://plone.com/secure" data-mce-href="https://plone.com/secure">the best security track record</a>, bar none. Written in Python and using a dependable NoSQL database, CastleCMS is not vulnerable to the all-too-common attacks that afflict&nbsp;PHP and SQL systems. But CastleCMS is more than&nbsp;just that: it&nbsp;is a marriage of technologies and ready-to-go integrated services that provides a complete out of the box solution for organizations with&nbsp;sophisticated needs and demanding security and scalability&nbsp;requirements.&nbsp;</p>
                    """  # noqa

    TWO_WIDE_1_2 = u"""
                    <h4>Who built CastleCMS?</h4>
                    <p>CastleCMS was developed&nbsp;by a highly experienced team&nbsp;from <a title="Wildcard Corp., the high security web technology solutions company" href="https://wildcardcorp.com" target="_blank" data-linktype="external" data-urltype="/view" data-val="https://wildcardcorp.com" data-mce-href="https://wildcardcorp.com">Wildcard Corp.</a>, a web development and hosting company located in Stevens Point, Wisconsin. Wildcard Corp. has a 10 year&nbsp;history of&nbsp;providing highly secure, robust systems to large government agencies. Our team includes core contributors and leaders&nbsp;of&nbsp;the open source <a title="Plone, the ultimate open source enterprise content management system" href="https://plone.com" target="_blank" data-linktype="external" data-urltype="/view" data-val="https://plone.com" data-mce-href="https://plone.com">Plone CMS</a>&nbsp;and <a title="The Plone community, bringing you the ultimate open source content management system" href="https://plone.org" target="_blank" data-linktype="external" data-urltype="/view" data-val="https://plone.org" data-mce-href="https://plone.org">community</a>. We combined our Plone and <a title="Wildcard Corp. success stories" href="https://wildcardcorp.com/success-stories" target="_blank" data-linktype="external" data-urltype="/view" data-val="https://wildcardcorp.com/success-stories" data-mce-href="https://wildcardcorp.com/success-stories">large government systems</a> experience to bring you&nbsp;an even better integrated CMS.</p>
                    """  # noqa

    TWO_WIDE_2_1 = u"""
                    <h4>What kind of support is available for CastleCMS?</h4>
                    <p>CastleCMS is currently available as a tiered cloud-hosted solution, for corporate, local or state government, and federal government / enterprise levels. With the exception of specific integration components used by our largest clients, CastleCMS will be open sourced, giving you the freedom to inspect, enhance, and modify it, and the ability to avoid vendor lock-in. Wildcard Corp.&nbsp;has earned rave reviews from some of the most demanding organizations for its outstanding&nbsp;proactive support.&nbsp;For more information on our support levels, please fill out our no-obligation <a data-val="410ec18805c44056813340350594a777" title="Quote Request Form" data-linktype="internal" href="https://castlecms.io/contact" data-mce-href="resolveuid/410ec18805c44056813340350594a777" data-urltype="_direct_">quote request form</a>.</p>
                    """  # noqa
    TWO_WIDE_2_2 = u"""
                    <h4>How much does CastleCMS cost?</h4>
                    <p>Each CastleCMS project is a custom-developed solution, and each client&#39;s needs vary greatly. We take great pride in being able to integrate CastleCMS with your existing systems and in providing you with design, customization, training, documentation, and support you can rely on.&nbsp;Please contact us&nbsp;for a no-obligation quote, either by emailing us at&nbsp;<a href="mailto:info@wildcardcorp.com?subject=CastleCMS%20Quote" data-linktype="email" data-urltype="/view" data-val="info@wildcardcorp.com" data-subject="CastleCMS Quote" data-mce-href="mailto:info@wildcardcorp.com?subject=CastleCMS Quote">info@wildcardcorp.com</a>,&nbsp;calling us at <a href="tel:+1%20(715)%20869-3440" data-linktype="external" data-urltype="/view" data-val="tel:+17158693440" data-mce-href="tel:+1 (715) 869-3440">+1 (715) 869-3440</a>, or filling out our <a data-val="410ec18805c44056813340350594a777" title="Quote Request Form" data-linktype="internal" href="https://castlecms.io/contact" data-mce-href="resolveuid/410ec18805c44056813340350594a777" data-urltype="_direct_">quote request form</a>. We look forward to hearing about&nbsp;your project requirements and being a part of your solution!</p>
                    """  # noqa

    FAQS = u"""<h3 style="text-align: center;" data-mce-style="text-align: center;">FREQUENTLY ASKED QUESTIONS<br></h3>"""  # noqa

    FEATURED_HIGHLIGHTS = u"""<h3 data-mce-style="text-align: center;" style="text-align: center;">FEATURE HIGHLIGHTS<br></h3>"""  # noqa

    FRONTPAGE_TILES = [
        {
            'data': {
                'content': TOP_FULL_WIDTH
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'title-top'
            }
        },
        {
            'data': {
                'content': THREE_WIDE_1
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'three-wide-1'
            }
        },
        {
            'data': {
                'content': THREE_WIDE_2
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'three-wide-2'
            }
        },
        {
            'data': {
                'content': THREE_WIDE_3
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'three-wide-3'
            }
        },
        {
            'data': {
                'content': TRY_CASTLE
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'try-castle'
            }
        },
        {
            'data': {
                'content': TWO_WIDE_1_1
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'bottom-1'
            }
        },
        {
            'data': {
                'content': TWO_WIDE_1_2
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'bottom-2'
            }
        },
        {
            'data': {
                'content': TWO_WIDE_2_1
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'bottom-3'
            }
        },
        {
            'data': {
                'content': TWO_WIDE_2_2
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'bottom-4'
            }
        },
        {
            'data': {
                'content': FAQS
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'faqs'
            }
        },
        {
            'data': {
                'content': FEATURED_HIGHLIGHTS
            },
            'meta': {
                'type': 'plone.app.standardtiles.rawhtml',
                'id': 'featured-highlights'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/tSwQ6XkSvgU',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-content-mgmt.png',
                'title': 'Intuitive Content Management',
                'text': RichTextValue("""<p>Creating, editing, and managing large amounts of content is easier than ever before with CastleCMS's newly-designed toolbar. Use drag and drop to upload and organize content effortlessly on your website. Filter content, apply tags, set publication and expiry dates, review and publish items, and grant specific permissions to users and groups, all using our powerful content management view.</p>
                            <p>Need to move massive amounts of content around your site? CastleCMS's asynchronous batch processing lets editors keep working as quickly as they need to.</p>
                            <p>CastleCMS also supports any number of simultaneously logged-in users and editors with absolutely no additional licensing fees.</p>
                        """)  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-1'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/wjRNcsxSShQ',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-security.png',
                'title': 'High Security',
                'text': RichTextValue("""<p>CastleCMS is based&nbsp;on Plone, which has&nbsp;the best security track record of any enterprise-scale content management system, but we have gone further, adding many&nbsp;security features to CastleCMS:</p>
                            <ul>
                                <li>built-in two-factor authentication that protects you from&nbsp;stolen password exploits&nbsp;</li>
                                <li>auto-lockout: after a&nbsp;maximum number of login attempts, users are automatically locked out</li>
                                <li>user session management that allows administrators to terminate suspicious sessions</li>
                                <li>a login-secured, customizable dashboard&nbsp;for each user</li>
                                <li>integrated reCAPTCHA to keep spammers and bots&nbsp;at bay</li>
                                <li>personally identifiable information (PII) and metadata are automatically stripped from uploaded Office documents, PDFs, and other file types</li>
                            </ul>
                            <p>CastleCMS&#39;s security is granular, letting&nbsp;you secure individual content items (pages, files, images, news items, calendar events) or entire sections of your site. If a user&nbsp;isn't&nbsp;authorized to access a content item, they won&#39;t even know it&#39;s there.</p>
                            <p>CastleCMS's&nbsp;built-in search engine knows what each person is authorized to see, so you can rest easy knowing that private data will remain that way.</p>
                        """)  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-2'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/ZJR_9Zqup2k',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-social-media.png',
                'title': 'Superior Social Media Integration',
                'text': RichTextValue("""<p>Embed tweets, Facebook statuses, timelines, and more as tiles that you can drag anywhere onto a page. CastleCMS&nbsp;includes &ldquo;Share on Facebook&rdquo; and &ldquo;Share on Twitter&rdquo; buttons that you can place anywhere on&nbsp;a&nbsp;site. CastleCMS&nbsp;even supports Twitter Cards, which allow you&mdash;and those that link to you&mdash;to attach rich photos, videos, and media to tweets. The best part about these features is that they are all available on any CastleCMS site right out of the box.</p>
                            <p>CastleCMS's built in search engine results are automatically adjusted&nbsp;according to&nbsp;your&nbsp;social media activity.</p>
                        """)  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-3'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/80bxHq-XmnY',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-page-preview.png',
                'title': 'Content Previews',
                'text': RichTextValue("""<p>If one of your pages doesn&#39;t look right, you can find out before it&#39;s too late. Page Preview allows you to see what your published pages will look like while they&#39;re still private, which could save you lots of embarrassment.</p>
                        """)  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-4'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/w8KuF06T608',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-layout-engine.png',
                'title': 'Dynamic Layout Engine',
                'text': RichTextValue("""<p>Create new layouts quickly and on a per&mdash;page basis. You can save and reuse&nbsp;them&nbsp;elsewhere on your site&nbsp;whenever you need to. Add columns as tiles that you can drag and drop into place.</p>
                        """)  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-5'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/Hj9qW34Hv4o',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-easy-theming.png',
                'title': 'Easy Theming',
                'text': RichTextValue("""<p>CastleCMS is extremely flexible for designers: its&nbsp;themes and designs are created&nbsp;using just&nbsp;a&nbsp;web browser, and you can&nbsp;set each individual page's design, or you can set a default design for sections of a site, or both. A CastleCMS site can be themed to match any existing website and&nbsp;to fit into an integrated suite of web services, making it easy to integrate&nbsp;CastleCMS-hosted content seamlessly.</p>
                        """)  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-6'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/zOVI65-TOI8',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-adv-toolbar.png',
                'title': 'Intuitive Toolbar',
                'text': RichTextValue("""<p>CastleCMS&#39;s toolbar was created in&mdash;house by our user experience team. It is&nbsp;designed to place all editing&nbsp;controls at your fingertips, intuitively and effectively.</p>
                        <p>Move content around, change its design or layout, share it with other users, access version history, examine its analytics data, even preview before you publish it.&nbsp;</p>""")  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-7'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/VakRVBIChOc',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-search.png',
                'title': 'Comprehensive Built-in Search',
                'text': RichTextValue("""<p>Every item in your site&mdash;whether a page, Office document, PDF, news item, event, video, or audio&mdash;is automatically and instantly searchable from the built&mdash;in search bar. Integrated optical character recognition (OCR) for all PDF, Word, Excel,&nbsp;PowerPoint, and TIFF image&nbsp;files automatically makes all your uploaded documents searchable using&nbsp;the&nbsp;built in Elasticsearch engine, which is robust&nbsp;and&nbsp;fast&nbsp;enough to handle sites with millions of content items.</p>
                        <p>Tag your content with keywords&nbsp;to make everything even easier to find. You can also search for content according to its title, description, body text, author, editor, date, and more.</p>""")  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-8'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/SnOId_MT5H0',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-seo.png',
                'title': 'Search Engine Optimization',
                'text': RichTextValue("""<p>CastleCMS generates semantic&nbsp;HTML5, ensuring that Google and other search engines correctly interpret the structure and content of your&nbsp;website. You can&nbsp;achieve higher organic search results&nbsp;for any given page&nbsp;by&nbsp;setting&nbsp;SEO keywords and meta tags, which give hints to&nbsp;search engines as to what a web page is about.</p>
                        <p>Even if you have many contributors and editors, CastleCMS helps you keep your site content under control by preventing anyone from uploading the same image or document twice&nbsp;and also by&nbsp;automatically uploading files&nbsp;to a central repository.</p>
                        <p>Your content can also be automatically archived after a set&nbsp;number of days, with&nbsp;each type of content&nbsp;having its own&nbsp;archival delay. Once archived, your content is stored in inexpensive Amazon Simple Storage Service (S3) bulk cloud storage, while&nbsp;remaining seamlessly available&nbsp;to your users at the same apparent web addresses. You can even have CastleCMS move bulky content automatically to S3 if it exceeds a certain size.</p>""")  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-9'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/N3z9d76Wk1E',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-doc-viewer.png',
                'title': 'A Viewer for All File Types',
                'text': RichTextValue("""<p>CastleCMS's built-in&nbsp;document viewer works much like Adobe Reader, allowing&nbsp;you to view PDF, Word, Excel, and many other file types without ever leaving your browser. Your users won&#39;t need any locally installed programs to view or search through documents on your website.</p>
                        <p>CastleCMS&#39;s document viewer includes dynamic search, so you can find a specific page within a document quickly and easily. It&nbsp;supports optical character recognition (OCR), turning scanned image files into searchable text documents. PDF conversion, available with the&nbsp;CastleCMS Cloud hosted service, turns all uploaded Office files into platform&mdash;independent PDFs.</p>""")  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-10'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/zacn1repAFk',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-quality-check.png',
                'title': 'Content Quality Assurance',
                'text': RichTextValue("""<p>Like your own personal proofreader, CastleCMS can suggest content edits and provide inline content analysis checks. CastleCMS includes&nbsp;a spell-check feature, a must&mdash;have&nbsp;for creating and maintaining high quality website content.</p>
                        <p>CastleCMS's automatic content quality checking helps you&nbsp;improve&nbsp;content&nbsp;before it is published. This helps to improve your organic SEO.&nbsp;</p>
                        <p>CastleCMS also provides content analytics out of the box like no other CMS. Examine analytics for the entire site, or just portions of your site,&nbsp;and see real&mdash;time statistics. CastleCMS queries Google Analytics directly and puts the information at your fingertips by displaying&nbsp;it&nbsp;directly on the page you are editing.</p>""")  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-11'
            }
        },
        {
            'data': {
                'youtube_url': u'https://youtu.be/7U29U7KmlNI',
                'icon_link': u'/++theme++castle.theme/img/frontpage/icon-rich-content.png',
                'title': 'Rich Content Editing',
                'text': RichTextValue("""<p>CastleCMS uses TinyMCE, the state of the art in what-you-see-is-what-you-get (WYSIWYG) web editors. Change formatting, bold text, italicize text, edit images, and even embed videos right from the editor. Your videos are automatically converted to a web compatible video format. You don&#39;t need to know CSS or HTML to&nbsp;write beautiful content. Everything is in plain English for your convenience.</p>
                        <p>But since we know not everyone&nbsp;reads&nbsp;English, CastleCMS&#39;s editing and control interface supports more than 64 other languages as well, so international and multilingual users and content editors&nbsp;are at home&nbsp;on your&nbsp;website.</p>""")  # noqa
            },
            'meta': {
                'type': 'castle.cms.feature',
                'id': 'fp-feature-12'
            }
        },
        {
            'data': {
                'fragment': 'coverimage'
            },
            'meta': {
                'type': 'castle.cms.fragment',
                'id': 'top-fragment'
            },
            'slot': 'top'
        }
    ]

    return FRONTPAGE_TILES
